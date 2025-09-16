import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, ManyToOne, JoinColumn } from 'typeorm'
import { Order } from './order.entity'

export enum ShipmentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  SHIPPED = 'shipped',
  IN_TRANSIT = 'in_transit',
  OUT_FOR_DELIVERY = 'out_for_delivery',
  DELIVERED = 'delivered',
  FAILED_DELIVERY = 'failed_delivery',
  RETURNED = 'returned'
}

export enum ShippingMethod {
  STANDARD = 'standard',
  EXPRESS = 'express',
  PICKUP = 'pickup'
}

@Entity('shipments')
export class Shipment {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column({ unique: true })
  trackingNumber: string

  @Column({ type: 'enum', enum: ShipmentStatus, default: ShipmentStatus.PENDING })
  status: ShipmentStatus

  @Column({ type: 'enum', enum: ShippingMethod, default: ShippingMethod.STANDARD })
  method: ShippingMethod

  @Column({ nullable: true })
  carrier: string

  @Column({ nullable: true })
  carrierTrackingNumber: string

  @Column({ type: 'decimal', precision: 8, scale: 3, nullable: true })
  weight: number

  @Column({ type: 'decimal', precision: 10, scale: 2, nullable: true })
  shippingCost: number

  @Column({ default: 'XAF' })
  currency: string

  // Addresses
  @Column({ type: 'json' })
  fromAddress: {
    name: string
    address: string
    city: string
    region: string
    postalCode?: string
    country: string
    phone?: string
  }

  @Column({ type: 'json' })
  toAddress: {
    name: string
    address: string
    city: string
    region: string
    postalCode?: string
    country: string
    phone?: string
  }

  // Tracking events
  @Column({ type: 'json', nullable: true })
  trackingEvents: Array<{
    status: string
    description: string
    location?: string
    timestamp: Date
  }>

  // Dates
  @Column({ nullable: true })
  shippedAt: Date

  @Column({ nullable: true })
  estimatedDeliveryDate: Date

  @Column({ nullable: true })
  deliveredAt: Date

  @Column({ type: 'text', nullable: true })
  notes: string

  @CreateDateColumn()
  createdAt: Date

  @UpdateDateColumn()
  updatedAt: Date

  // Relations
  @ManyToOne(() => Order, order => order.shipments)
  @JoinColumn({ name: 'orderId' })
  order: Order

  @Column()
  orderId: string
}
