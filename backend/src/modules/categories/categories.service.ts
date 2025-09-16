import { Injectable, NotFoundException } from '@nestjs/common'
import { InjectRepository } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { Category } from '../../database/entities/category.entity'

@Injectable()
export class CategoriesService {
  constructor(
    @InjectRepository(Category)
    private categoryRepository: Repository<Category>,
  ) {}

  async findAll(): Promise<Category[]> {
    return this.categoryRepository.find({
      where: { isActive: true },
      relations: ['parent', 'children'],
      order: { sortOrder: 'ASC', name: 'ASC' }
    })
  }

  async findRootCategories(): Promise<Category[]> {
    return this.categoryRepository.find({
      where: { 
        isActive: true,
        parentId: null 
      },
      relations: ['children'],
      order: { sortOrder: 'ASC', name: 'ASC' }
    })
  }

  async findFeatured(): Promise<Category[]> {
    return this.categoryRepository.find({
      where: { 
        isActive: true,
        isFeatured: true 
      },
      relations: ['children'],
      order: { sortOrder: 'ASC', name: 'ASC' }
    })
  }

  async findOne(id: string): Promise<Category> {
    const category = await this.categoryRepository.findOne({
      where: { id },
      relations: ['parent', 'children', 'products']
    })

    if (!category) {
      throw new NotFoundException(`Category with ID ${id} not found`)
    }

    return category
  }

  async findBySlug(slug: string): Promise<Category> {
    const category = await this.categoryRepository.findOne({
      where: { slug, isActive: true },
      relations: ['parent', 'children', 'products']
    })

    if (!category) {
      throw new NotFoundException(`Category with slug ${slug} not found`)
    }

    return category
  }

  async findChildren(parentId: string): Promise<Category[]> {
    return this.categoryRepository.find({
      where: { 
        parentId,
        isActive: true 
      },
      relations: ['children'],
      order: { sortOrder: 'ASC', name: 'ASC' }
    })
  }

  async getCategoryTree(): Promise<Category[]> {
    const categories = await this.categoryRepository.find({
      where: { isActive: true },
      relations: ['children'],
      order: { sortOrder: 'ASC', name: 'ASC' }
    })

    // Build tree structure
    const categoryMap = new Map<string, Category>()
    const rootCategories: Category[] = []

    // First pass: create map
    categories.forEach(category => {
      categoryMap.set(category.id, { ...category, children: [] })
    })

    // Second pass: build tree
    categories.forEach(category => {
      const categoryNode = categoryMap.get(category.id)!
      
      if (category.parentId) {
        const parent = categoryMap.get(category.parentId)
        if (parent) {
          parent.children.push(categoryNode)
        }
      } else {
        rootCategories.push(categoryNode)
      }
    })

    return rootCategories
  }

  async getCategoryStats(): Promise<{
    total: number
    active: number
    featured: number
    withProducts: number
  }> {
    const [total, active, featured, withProducts] = await Promise.all([
      this.categoryRepository.count(),
      this.categoryRepository.count({ where: { isActive: true } }),
      this.categoryRepository.count({ where: { isActive: true, isFeatured: true } }),
      this.categoryRepository
        .createQueryBuilder('category')
        .leftJoin('category.products', 'product')
        .where('category.isActive = :isActive', { isActive: true })
        .andWhere('product.id IS NOT NULL')
        .getCount()
    ])

    return { total, active, featured, withProducts }
  }
}
