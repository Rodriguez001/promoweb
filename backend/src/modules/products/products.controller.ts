import { Controller, Get, Query, Param, ParseUUIDPipe } from '@nestjs/common'
import { ApiTags, ApiOperation, ApiQuery, ApiResponse } from '@nestjs/swagger'
import { ProductsService, ProductFilters, ProductSearchOptions } from './products.service'
import { Product } from '../../database/entities/product.entity'

@ApiTags('products')
@Controller('products')
export class ProductsController {
  constructor(private readonly productsService: ProductsService) {}

  @Get()
  @ApiOperation({ summary: 'Get all products with filtering and pagination' })
  @ApiQuery({ name: 'page', required: false, type: Number })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiQuery({ name: 'category', required: false, type: String })
  @ApiQuery({ name: 'brand', required: false, type: String })
  @ApiQuery({ name: 'minPrice', required: false, type: Number })
  @ApiQuery({ name: 'maxPrice', required: false, type: Number })
  @ApiQuery({ name: 'search', required: false, type: String })
  @ApiQuery({ name: 'sortBy', required: false, enum: ['name', 'price', 'createdAt', 'rating'] })
  @ApiQuery({ name: 'sortOrder', required: false, enum: ['ASC', 'DESC'] })
  @ApiResponse({ status: 200, description: 'Products retrieved successfully' })
  async findAll(
    @Query('page') page?: number,
    @Query('limit') limit?: number,
    @Query('category') category?: string,
    @Query('brand') brand?: string,
    @Query('minPrice') minPrice?: number,
    @Query('maxPrice') maxPrice?: number,
    @Query('search') search?: string,
    @Query('inStock') inStock?: boolean,
    @Query('sortBy') sortBy?: 'name' | 'price' | 'createdAt' | 'rating',
    @Query('sortOrder') sortOrder?: 'ASC' | 'DESC',
  ) {
    const filters: ProductFilters = {
      category,
      brand,
      minPrice,
      maxPrice,
      search,
      inStock,
    }

    const options: ProductSearchOptions = {
      page,
      limit,
      sortBy,
      sortOrder,
    }

    return this.productsService.findAll(filters, options)
  }

  @Get('featured')
  @ApiOperation({ summary: 'Get featured products' })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiResponse({ status: 200, description: 'Featured products retrieved successfully' })
  async findFeatured(@Query('limit') limit?: number): Promise<Product[]> {
    return this.productsService.findFeatured(limit)
  }

  @Get('new')
  @ApiOperation({ summary: 'Get new products' })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiResponse({ status: 200, description: 'New products retrieved successfully' })
  async findNew(@Query('limit') limit?: number): Promise<Product[]> {
    return this.productsService.findNew(limit)
  }

  @Get('bestsellers')
  @ApiOperation({ summary: 'Get bestseller products' })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiResponse({ status: 200, description: 'Bestseller products retrieved successfully' })
  async findBestsellers(@Query('limit') limit?: number): Promise<Product[]> {
    return this.productsService.findBestsellers(limit)
  }

  @Get('search')
  @ApiOperation({ summary: 'Search products' })
  @ApiQuery({ name: 'q', required: true, type: String })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiResponse({ status: 200, description: 'Search results retrieved successfully' })
  async searchProducts(
    @Query('q') query: string,
    @Query('limit') limit?: number,
  ): Promise<Product[]> {
    return this.productsService.searchProducts(query, limit)
  }

  @Get('stats')
  @ApiOperation({ summary: 'Get product statistics' })
  @ApiResponse({ status: 200, description: 'Product statistics retrieved successfully' })
  async getStats() {
    return this.productsService.getProductStats()
  }

  @Get('category/:categoryId')
  @ApiOperation({ summary: 'Get products by category' })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiResponse({ status: 200, description: 'Products by category retrieved successfully' })
  async findByCategory(
    @Param('categoryId', ParseUUIDPipe) categoryId: string,
    @Query('limit') limit?: number,
  ): Promise<Product[]> {
    return this.productsService.findByCategory(categoryId, limit)
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get product by ID' })
  @ApiResponse({ status: 200, description: 'Product retrieved successfully' })
  @ApiResponse({ status: 404, description: 'Product not found' })
  async findOne(@Param('id', ParseUUIDPipe) id: string): Promise<Product> {
    return this.productsService.findOne(id)
  }
}
