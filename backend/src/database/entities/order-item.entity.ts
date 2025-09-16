import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, ManyToOne, JoinColumn } from 'typeorm'
import { Product } from './product.entity'

@Entity('order_items')
export class OrderItem {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column({ type: 'int' })
  quantity: number

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  unitPrice: number

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  totalPrice: number

  @Column({ default: 'XAF' })
  currency: string

  // Product snapshot at time of order
  @Column()
  productName: string

  @Column()
  productBrand: string

  @Column({ nullable: true })
  productSku: string

  @Column({ nullable: true })
  productImage: string

  @CreateDateColumn()
  createdAt: Date

  @UpdateDateColumn()
  updatedAt: Date

  // Relations
  @ManyToOne('Order', 'items', { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'orderId' })
  order: any

  @Column()
  orderId: string

  @ManyToOne(() => Product, product => product.orderItems)
  @JoinColumn({ name: 'productId' })
  product: Product

  @Column()
  productId: string
}
