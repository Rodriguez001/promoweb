import { Controller, Get, Param, ParseUUIDPipe } from '@nestjs/common'
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger'
import { CategoriesService } from './categories.service'
import { Category } from '../../database/entities/category.entity'

@ApiTags('categories')
@Controller('categories')
export class CategoriesController {
  constructor(private readonly categoriesService: CategoriesService) {}

  @Get()
  @ApiOperation({ summary: 'Get all active categories' })
  @ApiResponse({ status: 200, description: 'Categories retrieved successfully' })
  async findAll(): Promise<Category[]> {
    return this.categoriesService.findAll()
  }

  @Get('root')
  @ApiOperation({ summary: 'Get root categories (no parent)' })
  @ApiResponse({ status: 200, description: 'Root categories retrieved successfully' })
  async findRootCategories(): Promise<Category[]> {
    return this.categoriesService.findRootCategories()
  }

  @Get('featured')
  @ApiOperation({ summary: 'Get featured categories' })
  @ApiResponse({ status: 200, description: 'Featured categories retrieved successfully' })
  async findFeatured(): Promise<Category[]> {
    return this.categoriesService.findFeatured()
  }

  @Get('tree')
  @ApiOperation({ summary: 'Get category tree structure' })
  @ApiResponse({ status: 200, description: 'Category tree retrieved successfully' })
  async getCategoryTree(): Promise<Category[]> {
    return this.categoriesService.getCategoryTree()
  }

  @Get('stats')
  @ApiOperation({ summary: 'Get category statistics' })
  @ApiResponse({ status: 200, description: 'Category statistics retrieved successfully' })
  async getStats() {
    return this.categoriesService.getCategoryStats()
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get category by ID' })
  @ApiResponse({ status: 200, description: 'Category retrieved successfully' })
  @ApiResponse({ status: 404, description: 'Category not found' })
  async findOne(@Param('id', ParseUUIDPipe) id: string): Promise<Category> {
    return this.categoriesService.findOne(id)
  }

  @Get(':id/children')
  @ApiOperation({ summary: 'Get category children' })
  @ApiResponse({ status: 200, description: 'Category children retrieved successfully' })
  async findChildren(@Param('id', ParseUUIDPipe) id: string): Promise<Category[]> {
    return this.categoriesService.findChildren(id)
  }

  @Get('slug/:slug')
  @ApiOperation({ summary: 'Get category by slug' })
  @ApiResponse({ status: 200, description: 'Category retrieved successfully' })
  @ApiResponse({ status: 404, description: 'Category not found' })
  async findBySlug(@Param('slug') slug: string): Promise<Category> {
    return this.categoriesService.findBySlug(slug)
  }
}
