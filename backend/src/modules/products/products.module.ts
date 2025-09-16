import { Module } from '@nestjs/common'
import { TypeOrmModule } from '@nestjs/typeorm'
import { Product } from '../../database/entities/product.entity'
import { Category } from '../../database/entities/category.entity'
import { ProductsController } from './products.controller'
import { ProductsService } from './products.service'

@Module({
  imports: [TypeOrmModule.forFeature([Product, Category])],
  controllers: [ProductsController],
  providers: [ProductsService],
  exports: [ProductsService],
})
export class ProductsModule {}
