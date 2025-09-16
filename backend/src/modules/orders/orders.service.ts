import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common'
import { InjectRepository } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { Order, OrderStatus, PaymentStatus } from '../../database/entities/order.entity'
import { OrderItem } from '../../database/entities/order-item.entity'
import { Product } from '../../database/entities/product.entity'
import { ProductsService } from '../products/products.service'

export interface CreateOrderDto {
  userId?: string
  customerEmail: string
  customerPhone: string
  customerFirstName: string
  customerLastName: string
  shippingAddress: string
  shippingCity: string
  shippingRegion: string
  shippingPostalCode?: string
  items: Array<{
    productId: string
    quantity: number
  }>
  notes?: string
  depositPercentage?: number
}

export interface OrderFilters {
  status?: OrderStatus
  paymentStatus?: PaymentStatus
  userId?: string
  dateFrom?: Date
  dateTo?: Date
}

@Injectable()
export class OrdersService {
  constructor(
    @InjectRepository(Order)
    private orderRepository: Repository<Order>,
    @InjectRepository(OrderItem)
    private orderItemRepository: Repository<OrderItem>,
    @InjectRepository(Product)
    private productRepository: Repository<Product>,
    private productsService: ProductsService,
  ) {}

  async create(createOrderDto: CreateOrderDto): Promise<Order> {
    // Validate products and calculate totals
    let subtotal = 0
    const orderItems: Partial<OrderItem>[] = []

    for (const item of createOrderDto.items) {
      const product = await this.productsService.findOne(item.productId)
      
      if (!product.isInStock) {
        throw new BadRequestException(`Product ${product.name} is not in stock`)
      }

      if (product.availableQuantity < item.quantity) {
        throw new BadRequestException(
          `Insufficient stock for ${product.name}. Available: ${product.availableQuantity}, Requested: ${item.quantity}`
        )
      }

      const itemTotal = product.priceXaf * item.quantity
      subtotal += itemTotal

      orderItems.push({
        productId: product.id,
        quantity: item.quantity,
        unitPrice: product.priceXaf,
        totalPrice: itemTotal,
        productName: product.name,
        productBrand: product.brand,
        productSku: product.sku,
        productImage: product.mainImage,
      })
    }

    // Calculate shipping cost (simplified - based on total weight)
    const totalWeight = await this.calculateTotalWeight(createOrderDto.items)
    const shippingCost = this.calculateShippingCost(totalWeight, createOrderDto.shippingRegion)
    
    const total = subtotal + shippingCost
    const depositPercentage = createOrderDto.depositPercentage || 30
    const depositAmount = (total * depositPercentage) / 100
    const remainingAmount = total - depositAmount

    // Generate order number
    const orderNumber = await this.generateOrderNumber()

    // Create order
    const order = this.orderRepository.create({
      orderNumber,
      userId: createOrderDto.userId,
      customerEmail: createOrderDto.customerEmail,
      customerPhone: createOrderDto.customerPhone,
      customerFirstName: createOrderDto.customerFirstName,
      customerLastName: createOrderDto.customerLastName,
      shippingAddress: createOrderDto.shippingAddress,
      shippingCity: createOrderDto.shippingCity,
      shippingRegion: createOrderDto.shippingRegion,
      shippingPostalCode: createOrderDto.shippingPostalCode,
      subtotal,
      shippingCost,
      total,
      depositAmount,
      remainingAmount,
      depositPercentage,
      notes: createOrderDto.notes,
      status: OrderStatus.PENDING,
      paymentStatus: PaymentStatus.PENDING,
    })

    const savedOrder = await this.orderRepository.save(order)

    // Create order items
    for (const itemData of orderItems) {
      const orderItem = this.orderItemRepository.create({
        ...itemData,
        orderId: savedOrder.id,
      })
      await this.orderItemRepository.save(orderItem)
    }

    // Reserve stock
    for (const item of createOrderDto.items) {
      await this.productsService.reserveStock(item.productId, item.quantity)
    }

    return this.findOne(savedOrder.id)
  }

  async findAll(filters: OrderFilters = {}): Promise<Order[]> {
    const queryBuilder = this.orderRepository
      .createQueryBuilder('order')
      .leftJoinAndSelect('order.items', 'items')
      .leftJoinAndSelect('items.product', 'product')
      .leftJoinAndSelect('order.user', 'user')

    if (filters.status) {
      queryBuilder.andWhere('order.status = :status', { status: filters.status })
    }

    if (filters.paymentStatus) {
      queryBuilder.andWhere('order.paymentStatus = :paymentStatus', { paymentStatus: filters.paymentStatus })
    }

    if (filters.userId) {
      queryBuilder.andWhere('order.userId = :userId', { userId: filters.userId })
    }

    if (filters.dateFrom) {
      queryBuilder.andWhere('order.createdAt >= :dateFrom', { dateFrom: filters.dateFrom })
    }

    if (filters.dateTo) {
      queryBuilder.andWhere('order.createdAt <= :dateTo', { dateTo: filters.dateTo })
    }

    return queryBuilder
      .orderBy('order.createdAt', 'DESC')
      .getMany()
  }

  async findOne(id: string): Promise<Order> {
    const order = await this.orderRepository.findOne({
      where: { id },
      relations: ['items', 'items.product', 'user', 'payments', 'shipments']
    })

    if (!order) {
      throw new NotFoundException(`Order with ID ${id} not found`)
    }

    return order
  }

  async findByOrderNumber(orderNumber: string): Promise<Order> {
    const order = await this.orderRepository.findOne({
      where: { orderNumber },
      relations: ['items', 'items.product', 'user', 'payments', 'shipments']
    })

    if (!order) {
      throw new NotFoundException(`Order with number ${orderNumber} not found`)
    }

    return order
  }

  async updateStatus(id: string, status: OrderStatus): Promise<Order> {
    const order = await this.findOne(id)
    order.status = status
    return this.orderRepository.save(order)
  }

  async updatePaymentStatus(id: string, paymentStatus: PaymentStatus): Promise<Order> {
    const order = await this.findOne(id)
    order.paymentStatus = paymentStatus
    return this.orderRepository.save(order)
  }

  async cancel(id: string, reason?: string): Promise<Order> {
    const order = await this.findOne(id)

    if (!order.canBeCancelled) {
      throw new BadRequestException('Order cannot be cancelled in its current status')
    }

    // Release reserved stock
    for (const item of order.items) {
      await this.productsService.releaseStock(item.productId, item.quantity)
    }

    order.status = OrderStatus.CANCELLED
    if (reason) {
      order.adminNotes = reason
    }

    return this.orderRepository.save(order)
  }

  async getOrderStats(): Promise<{
    total: number
    pending: number
    confirmed: number
    shipped: number
    delivered: number
    cancelled: number
    totalRevenue: number
    averageOrderValue: number
  }> {
    const [
      total,
      pending,
      confirmed,
      shipped,
      delivered,
      cancelled,
      revenueResult,
    ] = await Promise.all([
      this.orderRepository.count(),
      this.orderRepository.count({ where: { status: OrderStatus.PENDING } }),
      this.orderRepository.count({ where: { status: OrderStatus.CONFIRMED } }),
      this.orderRepository.count({ where: { status: OrderStatus.SHIPPED } }),
      this.orderRepository.count({ where: { status: OrderStatus.DELIVERED } }),
      this.orderRepository.count({ where: { status: OrderStatus.CANCELLED } }),
      this.orderRepository
        .createQueryBuilder('order')
        .select('SUM(order.total)', 'totalRevenue')
        .addSelect('AVG(order.total)', 'averageOrderValue')
        .where('order.status != :cancelledStatus', { cancelledStatus: OrderStatus.CANCELLED })
        .getRawOne(),
    ])

    return {
      total,
      pending,
      confirmed,
      shipped,
      delivered,
      cancelled,
      totalRevenue: parseFloat(revenueResult?.totalRevenue || '0'),
      averageOrderValue: parseFloat(revenueResult?.averageOrderValue || '0'),
    }
  }

  private async generateOrderNumber(): Promise<string> {
    const date = new Date()
    const year = date.getFullYear().toString().slice(-2)
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    
    const count = await this.orderRepository.count()
    const sequence = (count + 1).toString().padStart(4, '0')
    
    return `PW${year}${month}${day}${sequence}`
  }

  private async calculateTotalWeight(items: Array<{ productId: string; quantity: number }>): Promise<number> {
    let totalWeight = 0
    
    for (const item of items) {
      const product = await this.productsService.findOne(item.productId)
      totalWeight += (product.weight || 0) * item.quantity
    }
    
    return totalWeight
  }

  private calculateShippingCost(weight: number, region: string): number {
    // Simplified shipping calculation
    // In production, this would be more sophisticated
    const baseRate = region === 'Douala' || region === 'Yaoundé' ? 2000 : 3000
    const weightRate = Math.ceil(weight) * 500
    
    return baseRate + weightRate
  }
}
