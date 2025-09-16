import { Module } from '@nestjs/common'
import { TypeOrmModule } from '@nestjs/typeorm'
import { Order } from '../../database/entities/order.entity'
import { OrderItem } from '../../database/entities/order-item.entity'
import { Product } from '../../database/entities/product.entity'
import { User } from '../../database/entities/user.entity'
import { OrdersController } from './orders.controller'
import { OrdersService } from './orders.service'
import { ProductsModule } from '../products/products.module'

@Module({
  imports: [
    TypeOrmModule.forFeature([Order, OrderItem, Product, User]),
    ProductsModule,
  ],
  controllers: [OrdersController],
  providers: [OrdersService],
  exports: [OrdersService],
})
export class OrdersModule {}
