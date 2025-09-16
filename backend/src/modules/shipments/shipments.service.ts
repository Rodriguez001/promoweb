import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common'
import { InjectRepository } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { Shipment, ShipmentStatus, ShippingMethod } from '../../database/entities/shipment.entity'
import { Order, OrderStatus } from '../../database/entities/order.entity'
import { OrdersService } from '../orders/orders.service'

export interface CreateShipmentDto {
  orderId: string
  method: ShippingMethod
  carrier?: string
  weight?: number
  shippingCost?: number
  fromAddress: {
    name: string
    address: string
    city: string
    region: string
    postalCode?: string
    country: string
    phone?: string
  }
  toAddress: {
    name: string
    address: string
    city: string
    region: string
    postalCode?: string
    country: string
    phone?: string
  }
  estimatedDeliveryDate?: Date
  notes?: string
}

export interface UpdateTrackingDto {
  status: ShipmentStatus
  description: string
  location?: string
}

@Injectable()
export class ShipmentsService {
  constructor(
    @InjectRepository(Shipment)
    private shipmentRepository: Repository<Shipment>,
    @InjectRepository(Order)
    private orderRepository: Repository<Order>,
    private ordersService: OrdersService,
  ) {}

  async create(createShipmentDto: CreateShipmentDto): Promise<Shipment> {
    const order = await this.ordersService.findOne(createShipmentDto.orderId)
    
    if (order.status !== OrderStatus.CONFIRMED) {
      throw new BadRequestException('Can only create shipment for confirmed orders')
    }

    const trackingNumber = await this.generateTrackingNumber()

    const shipment = this.shipmentRepository.create({
      ...createShipmentDto,
      trackingNumber,
      status: ShipmentStatus.PENDING,
      trackingEvents: [{
        status: ShipmentStatus.PENDING,
        description: 'Shipment created',
        timestamp: new Date(),
      }],
    })

    const savedShipment = await this.shipmentRepository.save(shipment)

    // Update order status
    await this.ordersService.updateStatus(createShipmentDto.orderId, OrderStatus.PROCESSING)

    return savedShipment
  }

  async findAll(): Promise<Shipment[]> {
    return this.shipmentRepository.find({
      relations: ['order'],
      order: { createdAt: 'DESC' }
    })
  }

  async findOne(id: string): Promise<Shipment> {
    const shipment = await this.shipmentRepository.findOne({
      where: { id },
      relations: ['order']
    })

    if (!shipment) {
      throw new NotFoundException(`Shipment with ID ${id} not found`)
    }

    return shipment
  }

  async findByTrackingNumber(trackingNumber: string): Promise<Shipment> {
    const shipment = await this.shipmentRepository.findOne({
      where: { trackingNumber },
      relations: ['order']
    })

    if (!shipment) {
      throw new NotFoundException(`Shipment with tracking number ${trackingNumber} not found`)
    }

    return shipment
  }

  async findByOrder(orderId: string): Promise<Shipment[]> {
    return this.shipmentRepository.find({
      where: { orderId },
      order: { createdAt: 'ASC' }
    })
  }

  async updateStatus(id: string, status: ShipmentStatus, description?: string, location?: string): Promise<Shipment> {
    const shipment = await this.findOne(id)
    
    shipment.status = status
    
    // Add tracking event
    const trackingEvent = {
      status,
      description: description || this.getDefaultStatusDescription(status),
      location,
      timestamp: new Date(),
    }
    
    shipment.trackingEvents = [...(shipment.trackingEvents || []), trackingEvent]

    // Update specific status dates
    if (status === ShipmentStatus.SHIPPED && !shipment.shippedAt) {
      shipment.shippedAt = new Date()
      // Update order status
      await this.ordersService.updateStatus(shipment.orderId, OrderStatus.SHIPPED)
    } else if (status === ShipmentStatus.DELIVERED && !shipment.deliveredAt) {
      shipment.deliveredAt = new Date()
      // Update order status
      await this.ordersService.updateStatus(shipment.orderId, OrderStatus.DELIVERED)
    }

    return this.shipmentRepository.save(shipment)
  }

  async updateCarrierTracking(id: string, carrierTrackingNumber: string): Promise<Shipment> {
    const shipment = await this.findOne(id)
    shipment.carrierTrackingNumber = carrierTrackingNumber
    return this.shipmentRepository.save(shipment)
  }

  async addTrackingEvent(id: string, updateTrackingDto: UpdateTrackingDto): Promise<Shipment> {
    const shipment = await this.findOne(id)
    
    const trackingEvent = {
      ...updateTrackingDto,
      timestamp: new Date(),
    }
    
    shipment.trackingEvents = [...(shipment.trackingEvents || []), trackingEvent]
    
    // Update status if provided
    if (updateTrackingDto.status !== shipment.status) {
      shipment.status = updateTrackingDto.status
      
      // Update specific status dates
      if (updateTrackingDto.status === ShipmentStatus.SHIPPED && !shipment.shippedAt) {
        shipment.shippedAt = new Date()
        await this.ordersService.updateStatus(shipment.orderId, OrderStatus.SHIPPED)
      } else if (updateTrackingDto.status === ShipmentStatus.DELIVERED && !shipment.deliveredAt) {
        shipment.deliveredAt = new Date()
        await this.ordersService.updateStatus(shipment.orderId, OrderStatus.DELIVERED)
      }
    }

    return this.shipmentRepository.save(shipment)
  }

  async getShipmentStats(): Promise<{
    total: number
    pending: number
    processing: number
    shipped: number
    inTransit: number
    delivered: number
    failed: number
    averageDeliveryTime: number
  }> {
    const [
      total,
      pending,
      processing,
      shipped,
      inTransit,
      delivered,
      failed,
      deliveryTimeResult,
    ] = await Promise.all([
      this.shipmentRepository.count(),
      this.shipmentRepository.count({ where: { status: ShipmentStatus.PENDING } }),
      this.shipmentRepository.count({ where: { status: ShipmentStatus.PROCESSING } }),
      this.shipmentRepository.count({ where: { status: ShipmentStatus.SHIPPED } }),
      this.shipmentRepository.count({ where: { status: ShipmentStatus.IN_TRANSIT } }),
      this.shipmentRepository.count({ where: { status: ShipmentStatus.DELIVERED } }),
      this.shipmentRepository.count({ where: { status: ShipmentStatus.FAILED_DELIVERY } }),
      this.shipmentRepository
        .createQueryBuilder('shipment')
        .select('AVG(EXTRACT(EPOCH FROM (shipment.deliveredAt - shipment.shippedAt)) / 86400)', 'avgDays')
        .where('shipment.status = :status', { status: ShipmentStatus.DELIVERED })
        .andWhere('shipment.shippedAt IS NOT NULL')
        .andWhere('shipment.deliveredAt IS NOT NULL')
        .getRawOne(),
    ])

    return {
      total,
      pending,
      processing,
      shipped,
      inTransit,
      delivered,
      failed,
      averageDeliveryTime: parseFloat(deliveryTimeResult?.avgDays || '0'),
    }
  }

  async simulateTracking(trackingNumber: string): Promise<Shipment> {
    const shipment = await this.findByTrackingNumber(trackingNumber)
    
    // Simulate tracking updates based on current status
    const currentStatus = shipment.status
    let nextStatus: ShipmentStatus
    let description: string
    let location: string

    switch (currentStatus) {
      case ShipmentStatus.PENDING:
        nextStatus = ShipmentStatus.PROCESSING
        description = 'Package is being prepared for shipment'
        location = 'Warehouse - Douala'
        break
      case ShipmentStatus.PROCESSING:
        nextStatus = ShipmentStatus.SHIPPED
        description = 'Package has been shipped'
        location = 'Distribution Center - Douala'
        break
      case ShipmentStatus.SHIPPED:
        nextStatus = ShipmentStatus.IN_TRANSIT
        description = 'Package is in transit'
        location = 'En route to destination'
        break
      case ShipmentStatus.IN_TRANSIT:
        nextStatus = ShipmentStatus.OUT_FOR_DELIVERY
        description = 'Package is out for delivery'
        location = shipment.toAddress.city
        break
      case ShipmentStatus.OUT_FOR_DELIVERY:
        nextStatus = ShipmentStatus.DELIVERED
        description = 'Package has been delivered'
        location = shipment.toAddress.city
        break
      default:
        return shipment // No further updates
    }

    return this.updateStatus(shipment.id, nextStatus, description, location)
  }

  private async generateTrackingNumber(): Promise<string> {
    const prefix = 'PW'
    const timestamp = Date.now().toString().slice(-8)
    const random = Math.random().toString(36).substring(2, 6).toUpperCase()
    return `${prefix}${timestamp}${random}`
  }

  private getDefaultStatusDescription(status: ShipmentStatus): string {
    const descriptions = {
      [ShipmentStatus.PENDING]: 'Shipment created and pending processing',
      [ShipmentStatus.PROCESSING]: 'Package is being prepared for shipment',
      [ShipmentStatus.SHIPPED]: 'Package has been shipped',
      [ShipmentStatus.IN_TRANSIT]: 'Package is in transit',
      [ShipmentStatus.OUT_FOR_DELIVERY]: 'Package is out for delivery',
      [ShipmentStatus.DELIVERED]: 'Package has been delivered successfully',
      [ShipmentStatus.FAILED_DELIVERY]: 'Delivery attempt failed',
      [ShipmentStatus.RETURNED]: 'Package has been returned to sender',
    }

    return descriptions[status] || 'Status updated'
  }
}
