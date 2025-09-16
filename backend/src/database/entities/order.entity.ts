import { Entity, PrimaryGeneratedColumn, Column, ManyToOne, OneToMany, CreateDateColumn, UpdateDateColumn, JoinColumn } from 'typeorm';
import { User } from './user.entity';
import { Payment } from './payment.entity';
import { Shipment } from './shipment.entity';

export enum OrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  PROCESSING = 'processing',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
  REFUNDED = 'refunded'
}

export enum PaymentStatus {
  PENDING = 'pending',
  DEPOSIT_PAID = 'deposit_paid',
  FULLY_PAID = 'fully_paid',
  FAILED = 'failed',
  REFUNDED = 'refunded'
}

@Entity('orders')
export class Order {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column({ unique: true })
  orderNumber: string

  @Column({ type: 'enum', enum: OrderStatus, default: OrderStatus.PENDING })
  status: OrderStatus

  @Column({ type: 'enum', enum: PaymentStatus, default: PaymentStatus.PENDING })
  paymentStatus: PaymentStatus

  // Pricing
  @Column({ type: 'decimal', precision: 10, scale: 2 })
  subtotal: number

  @Column({ type: 'decimal', precision: 10, scale: 2, default: 0 })
  shippingCost: number

  @Column({ type: 'decimal', precision: 10, scale: 2, default: 0 })
  taxAmount: number

  @Column({ type: 'decimal', precision: 10, scale: 2, default: 0 })
  discountAmount: number

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  total: number

  @Column({ default: 'XAF' })
  currency: string

  // Payment terms (acompte system)
  @Column({ type: 'decimal', precision: 10, scale: 2 })
  depositAmount: number

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  remainingAmount: number

  @Column({ type: 'decimal', precision: 5, scale: 2, default: 30 })
  depositPercentage: number

  // Customer information
  @Column()
  customerEmail: string

  @Column()
  customerPhone: string

  @Column()
  customerFirstName: string

  @Column()
  customerLastName: string

  // Shipping address
  @Column()
  shippingAddress: string

  @Column()
  shippingCity: string

  @Column()
  shippingRegion: string

  @Column({ nullable: true })
  shippingPostalCode: string

  @Column({ default: 'CM' })
  shippingCountry: string

  // Billing address (if different)
  @Column({ nullable: true })
  billingAddress: string

  @Column({ nullable: true })
  billingCity: string

  @Column({ nullable: true })
  billingRegion: string

  @Column({ nullable: true })
  billingPostalCode: string

  @Column({ nullable: true })
  billingCountry: string

  // Order notes and metadata
  @Column({ type: 'text', nullable: true })
  notes: string

  @Column({ type: 'text', nullable: true })
  adminNotes: string

  @Column({ type: 'json', nullable: true })
  metadata: Record<string, any>

  // Tracking
  @Column({ nullable: true })
  trackingNumber: string

  @Column({ nullable: true })
  estimatedDeliveryDate: Date

  @Column({ nullable: true })
  deliveredAt: Date

  @CreateDateColumn()
  createdAt: Date

  @UpdateDateColumn()
  updatedAt: Date

  // Relations
  @ManyToOne(() => User, user => user.orders, { nullable: true })
  @JoinColumn({ name: 'userId' })
  user: User

  @Column({ nullable: true })
  userId: string

  @OneToMany('OrderItem', 'order', { cascade: true })
  items: any[]

  @OneToMany(() => Payment, payment => payment.order)
  payments: Payment[]

  @OneToMany(() => Shipment, shipment => shipment.order)
  shipments: Shipment[]

  // Computed properties
  get isDeposit(): boolean {
    return this.depositPercentage > 0 && this.depositPercentage < 100
  }

  get isFullyPaid(): boolean {
    return this.paymentStatus === PaymentStatus.FULLY_PAID
  }

  get canBeCancelled(): boolean {
    return [OrderStatus.PENDING, OrderStatus.CONFIRMED].includes(this.status)
  }

  get totalWeight(): number {
    return this.items?.reduce((total, item) => total + (item.product?.weight || 0) * item.quantity, 0) || 0
  }
}
