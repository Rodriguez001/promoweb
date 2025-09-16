import { Module } from '@nestjs/common'
import { TypeOrmModule } from '@nestjs/typeorm'
import { Shipment } from '../../database/entities/shipment.entity'
import { Order } from '../../database/entities/order.entity'
import { ShipmentsController } from './shipments.controller'
import { ShipmentsService } from './shipments.service'
import { OrdersModule } from '../orders/orders.module'

@Module({
  imports: [
    TypeOrmModule.forFeature([Shipment, Order]),
    OrdersModule,
  ],
  controllers: [ShipmentsController],
  providers: [ShipmentsService],
  exports: [ShipmentsService],
})
export class ShipmentsModule {}
