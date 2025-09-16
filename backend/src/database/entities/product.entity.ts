import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, ManyToOne, OneToMany, JoinColumn } from 'typeorm'
import { Category } from './category.entity'
import { OrderItem } from './order-item.entity'

export enum ProductStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  OUT_OF_STOCK = 'out_of_stock',
  DISCONTINUED = 'discontinued'
}

@Entity('products')
export class Product {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column()
  name: string

  @Column({ type: 'text' })
  description: string

  @Column({ nullable: true })
  shortDescription: string

  @Column()
  brand: string

  @Column({ unique: true, nullable: true })
  sku: string

  @Column({ nullable: true })
  ean: string

  @Column({ nullable: true })
  isbn: string

  // Pricing in EUR (original European price)
  @Column({ type: 'decimal', precision: 10, scale: 2 })
  priceEur: number

  // Pricing in XAF (calculated with conversion + margins)
  @Column({ type: 'decimal', precision: 10, scale: 2 })
  priceXaf: number

  @Column({ type: 'decimal', precision: 10, scale: 2, nullable: true })
  originalPriceXaf: number

  @Column({ type: 'decimal', precision: 5, scale: 2, default: 0 })
  discountPercentage: number

  // Stock management
  @Column({ type: 'int', default: 0 })
  stockQuantity: number

  @Column({ type: 'int', default: 0 })
  reservedQuantity: number

  @Column({ type: 'int', default: 1 })
  minStockLevel: number

  @Column({ type: 'enum', enum: ProductStatus, default: ProductStatus.ACTIVE })
  status: ProductStatus

  // Physical properties
  @Column({ type: 'decimal', precision: 8, scale: 3, nullable: true })
  weight: number // in kg

  @Column({ type: 'decimal', precision: 8, scale: 3, nullable: true })
  length: number // in cm

  @Column({ type: 'decimal', precision: 8, scale: 3, nullable: true })
  width: number // in cm

  @Column({ type: 'decimal', precision: 8, scale: 3, nullable: true })
  height: number // in cm

  // Images
  @Column({ type: 'json', nullable: true })
  images: string[]

  @Column({ nullable: true })
  mainImage: string

  // SEO and metadata
  @Column({ nullable: true })
  metaTitle: string

  @Column({ type: 'text', nullable: true })
  metaDescription: string

  @Column({ type: 'json', nullable: true })
  tags: string[]

  // Product features
  @Column({ type: 'json', nullable: true })
  features: Record<string, any>

  @Column({ type: 'json', nullable: true })
  specifications: Record<string, any>

  // Ratings and reviews
  @Column({ type: 'decimal', precision: 3, scale: 2, default: 0 })
  averageRating: number

  @Column({ type: 'int', default: 0 })
  reviewCount: number

  // Flags
  @Column({ default: false })
  isFeatured: boolean

  @Column({ default: false })
  isNew: boolean

  @Column({ default: false })
  isBestseller: boolean

  // External sync
  @Column({ nullable: true })
  externalId: string

  @Column({ nullable: true })
  externalSource: string // 'google_merchant', 'api', 'manual'

  @Column({ nullable: true })
  lastSyncAt: Date

  @CreateDateColumn()
  createdAt: Date

  @UpdateDateColumn()
  updatedAt: Date

  // Relations
  @ManyToOne(() => Category, category => category.products)
  @JoinColumn({ name: 'categoryId' })
  category: Category

  @Column({ nullable: true })
  categoryId: string

  @OneToMany(() => OrderItem, orderItem => orderItem.product)
  orderItems: OrderItem[]

  // Computed properties
  get isInStock(): boolean {
    return this.stockQuantity > this.reservedQuantity && this.status === ProductStatus.ACTIVE
  }

  get availableQuantity(): number {
    return Math.max(0, this.stockQuantity - this.reservedQuantity)
  }

  get hasDiscount(): boolean {
    return this.discountPercentage > 0 && this.originalPriceXaf > 0
  }
}
