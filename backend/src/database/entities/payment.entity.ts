import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, ManyToOne, JoinColumn } from 'typeorm'
import { Order } from './order.entity'

export enum PaymentMethod {
  ORANGE_MONEY = 'orange_money',
  MTN_MOBILE_MONEY = 'mtn_mobile_money',
  CREDIT_CARD = 'credit_card',
  BANK_TRANSFER = 'bank_transfer',
  CASH_ON_DELIVERY = 'cash_on_delivery'
}

export enum PaymentType {
  DEPOSIT = 'deposit',
  BALANCE = 'balance',
  FULL = 'full',
  REFUND = 'refund'
}

export enum PaymentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  REFUNDED = 'refunded'
}

@Entity('payments')
export class Payment {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column({ unique: true })
  transactionId: string

  @Column({ type: 'enum', enum: PaymentMethod })
  method: PaymentMethod

  @Column({ type: 'enum', enum: PaymentType })
  type: PaymentType

  @Column({ type: 'enum', enum: PaymentStatus, default: PaymentStatus.PENDING })
  status: PaymentStatus

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  amount: number

  @Column({ default: 'XAF' })
  currency: string

  // Payment provider details
  @Column({ nullable: true })
  providerTransactionId: string

  @Column({ nullable: true })
  providerReference: string

  @Column({ type: 'json', nullable: true })
  providerResponse: Record<string, any>

  // Mobile Money specific
  @Column({ nullable: true })
  phoneNumber: string

  @Column({ nullable: true })
  operatorTransactionId: string

  // Card payment specific
  @Column({ nullable: true })
  cardLast4: string

  @Column({ nullable: true })
  cardBrand: string

  // Metadata
  @Column({ type: 'text', nullable: true })
  description: string

  @Column({ type: 'json', nullable: true })
  metadata: Record<string, any>

  @Column({ nullable: true })
  failureReason: string

  @Column({ nullable: true })
  processedAt: Date

  @CreateDateColumn()
  createdAt: Date

  @UpdateDateColumn()
  updatedAt: Date

  // Relations
  @ManyToOne(() => Order, order => order.payments)
  @JoinColumn({ name: 'orderId' })
  order: Order

  @Column()
  orderId: string
}
