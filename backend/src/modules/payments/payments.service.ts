import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common'
import { InjectRepository } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { Payment, PaymentMethod, PaymentType, PaymentStatus } from '../../database/entities/payment.entity'
import { Order, PaymentStatus as OrderPaymentStatus } from '../../database/entities/order.entity'
import { OrdersService } from '../orders/orders.service'

export interface CreatePaymentDto {
  orderId: string
  method: PaymentMethod
  type: PaymentType
  amount: number
  phoneNumber?: string
  description?: string
  metadata?: Record<string, any>
}

export interface ProcessMobileMoneyDto {
  orderId: string
  phoneNumber: string
  amount: number
  method: PaymentMethod.ORANGE_MONEY | PaymentMethod.MTN_MOBILE_MONEY
  type: PaymentType
}

@Injectable()
export class PaymentsService {
  constructor(
    @InjectRepository(Payment)
    private paymentRepository: Repository<Payment>,
    @InjectRepository(Order)
    private orderRepository: Repository<Order>,
    private ordersService: OrdersService,
  ) {}

  async create(createPaymentDto: CreatePaymentDto): Promise<Payment> {
    const order = await this.ordersService.findOne(createPaymentDto.orderId)
    
    // Validate payment amount
    if (createPaymentDto.type === PaymentType.DEPOSIT) {
      if (createPaymentDto.amount !== order.depositAmount) {
        throw new BadRequestException('Deposit amount does not match order deposit amount')
      }
    } else if (createPaymentDto.type === PaymentType.BALANCE) {
      if (createPaymentDto.amount !== order.remainingAmount) {
        throw new BadRequestException('Balance amount does not match order remaining amount')
      }
    } else if (createPaymentDto.type === PaymentType.FULL) {
      if (createPaymentDto.amount !== order.total) {
        throw new BadRequestException('Full payment amount does not match order total')
      }
    }

    const transactionId = await this.generateTransactionId()

    const payment = this.paymentRepository.create({
      ...createPaymentDto,
      transactionId,
      status: PaymentStatus.PENDING,
    })

    return this.paymentRepository.save(payment)
  }

  async processMobileMoney(processMobileMoneyDto: ProcessMobileMoneyDto): Promise<Payment> {
    const payment = await this.create({
      ...processMobileMoneyDto,
      description: `Mobile Money payment via ${processMobileMoneyDto.method}`,
    })

    // Simulate mobile money processing
    // In production, this would integrate with actual mobile money APIs
    try {
      const result = await this.simulateMobileMoneyPayment(payment)
      
      if (result.success) {
        payment.status = PaymentStatus.COMPLETED
        payment.providerTransactionId = result.transactionId
        payment.operatorTransactionId = result.operatorTransactionId
        payment.processedAt = new Date()
        
        // Update order payment status
        await this.updateOrderPaymentStatus(payment.orderId, payment.type)
      } else {
        payment.status = PaymentStatus.FAILED
        payment.failureReason = result.error
      }
    } catch (error) {
      payment.status = PaymentStatus.FAILED
      payment.failureReason = error.message
    }

    return this.paymentRepository.save(payment)
  }

  async processCardPayment(orderId: string, amount: number, type: PaymentType, cardToken: string): Promise<Payment> {
    const payment = await this.create({
      orderId,
      method: PaymentMethod.CREDIT_CARD,
      type,
      amount,
      description: 'Credit card payment',
      metadata: { cardToken },
    })

    // Simulate card processing
    // In production, this would integrate with payment processors like Stripe, PayPal, etc.
    try {
      const result = await this.simulateCardPayment(payment, cardToken)
      
      if (result.success) {
        payment.status = PaymentStatus.COMPLETED
        payment.providerTransactionId = result.transactionId
        payment.cardLast4 = result.cardLast4
        payment.cardBrand = result.cardBrand
        payment.processedAt = new Date()
        
        // Update order payment status
        await this.updateOrderPaymentStatus(payment.orderId, payment.type)
      } else {
        payment.status = PaymentStatus.FAILED
        payment.failureReason = result.error
      }
    } catch (error) {
      payment.status = PaymentStatus.FAILED
      payment.failureReason = error.message
    }

    return this.paymentRepository.save(payment)
  }

  async findAll(): Promise<Payment[]> {
    return this.paymentRepository.find({
      relations: ['order'],
      order: { createdAt: 'DESC' }
    })
  }

  async findOne(id: string): Promise<Payment> {
    const payment = await this.paymentRepository.findOne({
      where: { id },
      relations: ['order']
    })

    if (!payment) {
      throw new NotFoundException(`Payment with ID ${id} not found`)
    }

    return payment
  }

  async findByOrder(orderId: string): Promise<Payment[]> {
    return this.paymentRepository.find({
      where: { orderId },
      order: { createdAt: 'ASC' }
    })
  }

  async findByTransactionId(transactionId: string): Promise<Payment> {
    const payment = await this.paymentRepository.findOne({
      where: { transactionId },
      relations: ['order']
    })

    if (!payment) {
      throw new NotFoundException(`Payment with transaction ID ${transactionId} not found`)
    }

    return payment
  }

  async refund(paymentId: string, amount?: number): Promise<Payment> {
    const originalPayment = await this.findOne(paymentId)
    
    if (originalPayment.status !== PaymentStatus.COMPLETED) {
      throw new BadRequestException('Can only refund completed payments')
    }

    const refundAmount = amount || originalPayment.amount

    if (refundAmount > originalPayment.amount) {
      throw new BadRequestException('Refund amount cannot exceed original payment amount')
    }

    const refundPayment = this.paymentRepository.create({
      orderId: originalPayment.orderId,
      method: originalPayment.method,
      type: PaymentType.REFUND,
      amount: -refundAmount, // Negative amount for refund
      status: PaymentStatus.COMPLETED,
      transactionId: await this.generateTransactionId(),
      description: `Refund for payment ${originalPayment.transactionId}`,
      processedAt: new Date(),
    })

    return this.paymentRepository.save(refundPayment)
  }

  async getPaymentStats(): Promise<{
    total: number
    completed: number
    pending: number
    failed: number
    totalAmount: number
    totalRefunds: number
  }> {
    const [
      total,
      completed,
      pending,
      failed,
      amountResult,
      refundResult,
    ] = await Promise.all([
      this.paymentRepository.count(),
      this.paymentRepository.count({ where: { status: PaymentStatus.COMPLETED } }),
      this.paymentRepository.count({ where: { status: PaymentStatus.PENDING } }),
      this.paymentRepository.count({ where: { status: PaymentStatus.FAILED } }),
      this.paymentRepository
        .createQueryBuilder('payment')
        .select('SUM(payment.amount)', 'totalAmount')
        .where('payment.status = :status', { status: PaymentStatus.COMPLETED })
        .andWhere('payment.type != :refundType', { refundType: PaymentType.REFUND })
        .getRawOne(),
      this.paymentRepository
        .createQueryBuilder('payment')
        .select('SUM(ABS(payment.amount))', 'totalRefunds')
        .where('payment.status = :status', { status: PaymentStatus.COMPLETED })
        .andWhere('payment.type = :refundType', { refundType: PaymentType.REFUND })
        .getRawOne(),
    ])

    return {
      total,
      completed,
      pending,
      failed,
      totalAmount: parseFloat(amountResult?.totalAmount || '0'),
      totalRefunds: parseFloat(refundResult?.totalRefunds || '0'),
    }
  }

  private async updateOrderPaymentStatus(orderId: string, paymentType: PaymentType): Promise<void> {
    const order = await this.ordersService.findOne(orderId)
    const payments = await this.findByOrder(orderId)
    
    const completedPayments = payments.filter(p => p.status === PaymentStatus.COMPLETED && p.type !== PaymentType.REFUND)
    const totalPaid = completedPayments.reduce((sum, p) => sum + p.amount, 0)

    let newPaymentStatus: OrderPaymentStatus

    if (totalPaid >= order.total) {
      newPaymentStatus = OrderPaymentStatus.FULLY_PAID
    } else if (totalPaid >= order.depositAmount) {
      newPaymentStatus = OrderPaymentStatus.DEPOSIT_PAID
    } else {
      newPaymentStatus = OrderPaymentStatus.PENDING
    }

    await this.ordersService.updatePaymentStatus(orderId, newPaymentStatus)
  }

  private async generateTransactionId(): Promise<string> {
    const timestamp = Date.now().toString()
    const random = Math.random().toString(36).substring(2, 8).toUpperCase()
    return `PW${timestamp}${random}`
  }

  private async simulateMobileMoneyPayment(payment: Payment): Promise<{
    success: boolean
    transactionId?: string
    operatorTransactionId?: string
    error?: string
  }> {
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 2000))

    // Simulate 90% success rate
    if (Math.random() > 0.1) {
      return {
        success: true,
        transactionId: `MM${Date.now()}`,
        operatorTransactionId: `OP${Math.random().toString(36).substring(2, 10).toUpperCase()}`,
      }
    } else {
      return {
        success: false,
        error: 'Insufficient funds or network error',
      }
    }
  }

  private async simulateCardPayment(payment: Payment, cardToken: string): Promise<{
    success: boolean
    transactionId?: string
    cardLast4?: string
    cardBrand?: string
    error?: string
  }> {
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1500))

    // Simulate 95% success rate
    if (Math.random() > 0.05) {
      return {
        success: true,
        transactionId: `CC${Date.now()}`,
        cardLast4: '1234',
        cardBrand: 'Visa',
      }
    } else {
      return {
        success: false,
        error: 'Card declined or processing error',
      }
    }
  }
}
