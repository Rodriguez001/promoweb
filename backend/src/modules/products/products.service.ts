import { Injectable, NotFoundException } from '@nestjs/common'
import { InjectRepository } from '@nestjs/typeorm'
import { Repository, FindManyOptions, Like, In } from 'typeorm'
import { Product, ProductStatus } from '../../database/entities/product.entity'

export interface ProductFilters {
  category?: string
  brand?: string
  minPrice?: number
  maxPrice?: number
  inStock?: boolean
  status?: ProductStatus
  search?: string
  tags?: string[]
}

export interface ProductSearchOptions {
  page?: number
  limit?: number
  sortBy?: 'name' | 'price' | 'createdAt' | 'rating'
  sortOrder?: 'ASC' | 'DESC'
}

@Injectable()
export class ProductsService {
  constructor(
    @InjectRepository(Product)
    private productRepository: Repository<Product>,
  ) {}

  async findAll(
    filters: ProductFilters = {},
    options: ProductSearchOptions = {}
  ): Promise<{ products: Product[]; total: number; page: number; totalPages: number }> {
    const {
      page = 1,
      limit = 20,
      sortBy = 'createdAt',
      sortOrder = 'DESC'
    } = options

    const queryBuilder = this.productRepository
      .createQueryBuilder('product')
      .leftJoinAndSelect('product.category', 'category')

    // Apply filters
    if (filters.category) {
      queryBuilder.andWhere('category.slug = :category', { category: filters.category })
    }

    if (filters.brand) {
      queryBuilder.andWhere('product.brand ILIKE :brand', { brand: `%${filters.brand}%` })
    }

    if (filters.minPrice !== undefined) {
      queryBuilder.andWhere('product.priceXaf >= :minPrice', { minPrice: filters.minPrice })
    }

    if (filters.maxPrice !== undefined) {
      queryBuilder.andWhere('product.priceXaf <= :maxPrice', { maxPrice: filters.maxPrice })
    }

    if (filters.inStock) {
      queryBuilder.andWhere('product.stockQuantity > product.reservedQuantity')
    }

    if (filters.status) {
      queryBuilder.andWhere('product.status = :status', { status: filters.status })
    } else {
      queryBuilder.andWhere('product.status = :status', { status: ProductStatus.ACTIVE })
    }

    if (filters.search) {
      queryBuilder.andWhere(
        '(product.name ILIKE :search OR product.description ILIKE :search OR product.brand ILIKE :search)',
        { search: `%${filters.search}%` }
      )
    }

    if (filters.tags && filters.tags.length > 0) {
      queryBuilder.andWhere('product.tags && :tags', { tags: filters.tags })
    }

    // Apply sorting
    queryBuilder.orderBy(`product.${sortBy}`, sortOrder)

    // Apply pagination
    const offset = (page - 1) * limit
    queryBuilder.skip(offset).take(limit)

    const [products, total] = await queryBuilder.getManyAndCount()
    const totalPages = Math.ceil(total / limit)

    return {
      products,
      total,
      page,
      totalPages
    }
  }

  async findOne(id: string): Promise<Product> {
    const product = await this.productRepository.findOne({
      where: { id },
      relations: ['category']
    })

    if (!product) {
      throw new NotFoundException(`Product with ID ${id} not found`)
    }

    return product
  }

  async findBySlug(slug: string): Promise<Product> {
    const product = await this.productRepository.findOne({
      where: { sku: slug },
      relations: ['category']
    })

    if (!product) {
      throw new NotFoundException(`Product with slug ${slug} not found`)
    }

    return product
  }

  async findFeatured(limit: number = 8): Promise<Product[]> {
    return this.productRepository.find({
      where: {
        isFeatured: true,
        status: ProductStatus.ACTIVE
      },
      relations: ['category'],
      order: { createdAt: 'DESC' },
      take: limit
    })
  }

  async findNew(limit: number = 8): Promise<Product[]> {
    return this.productRepository.find({
      where: {
        isNew: true,
        status: ProductStatus.ACTIVE
      },
      relations: ['category'],
      order: { createdAt: 'DESC' },
      take: limit
    })
  }

  async findBestsellers(limit: number = 8): Promise<Product[]> {
    return this.productRepository.find({
      where: {
        isBestseller: true,
        status: ProductStatus.ACTIVE
      },
      relations: ['category'],
      order: { averageRating: 'DESC' },
      take: limit
    })
  }

  async findByCategory(categoryId: string, limit?: number): Promise<Product[]> {
    const options: FindManyOptions<Product> = {
      where: {
        categoryId,
        status: ProductStatus.ACTIVE
      },
      relations: ['category'],
      order: { createdAt: 'DESC' }
    }

    if (limit) {
      options.take = limit
    }

    return this.productRepository.find(options)
  }

  async searchProducts(query: string, limit: number = 20): Promise<Product[]> {
    return this.productRepository
      .createQueryBuilder('product')
      .leftJoinAndSelect('product.category', 'category')
      .where(
        'product.name ILIKE :query OR product.description ILIKE :query OR product.brand ILIKE :query OR product.sku ILIKE :query OR product.ean ILIKE :query OR product.isbn ILIKE :query',
        { query: `%${query}%` }
      )
      .andWhere('product.status = :status', { status: ProductStatus.ACTIVE })
      .orderBy('product.name', 'ASC')
      .take(limit)
      .getMany()
  }

  async updateStock(productId: string, quantity: number): Promise<Product> {
    const product = await this.findOne(productId)
    product.stockQuantity = quantity
    return this.productRepository.save(product)
  }

  async reserveStock(productId: string, quantity: number): Promise<boolean> {
    const product = await this.findOne(productId)
    
    if (product.availableQuantity < quantity) {
      return false
    }

    product.reservedQuantity += quantity
    await this.productRepository.save(product)
    return true
  }

  async releaseStock(productId: string, quantity: number): Promise<void> {
    const product = await this.findOne(productId)
    product.reservedQuantity = Math.max(0, product.reservedQuantity - quantity)
    await this.productRepository.save(product)
  }

  async getProductStats(): Promise<{
    total: number
    active: number
    outOfStock: number
    lowStock: number
  }> {
    const [total, active, outOfStock, lowStock] = await Promise.all([
      this.productRepository.count(),
      this.productRepository.count({ where: { status: ProductStatus.ACTIVE } }),
      this.productRepository.count({ where: { status: ProductStatus.OUT_OF_STOCK } }),
      this.productRepository
        .createQueryBuilder('product')
        .where('product.stockQuantity <= product.minStockLevel')
        .andWhere('product.status = :status', { status: ProductStatus.ACTIVE })
        .getCount()
    ])

    return { total, active, outOfStock, lowStock }
  }
}
