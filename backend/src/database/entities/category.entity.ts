import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, OneToMany, ManyToOne, JoinColumn } from 'typeorm'
import { Product } from './product.entity'

@Entity('categories')
export class Category {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column()
  name: string

  @Column({ unique: true })
  slug: string

  @Column({ type: 'text', nullable: true })
  description: string

  @Column({ nullable: true })
  icon: string

  @Column({ nullable: true })
  image: string

  @Column({ nullable: true })
  color: string

  @Column({ type: 'int', default: 0 })
  sortOrder: number

  @Column({ default: true })
  isActive: boolean

  @Column({ default: false })
  isFeatured: boolean

  // SEO
  @Column({ nullable: true })
  metaTitle: string

  @Column({ type: 'text', nullable: true })
  metaDescription: string

  // Hierarchy support
  @ManyToOne(() => Category, category => category.children, { nullable: true })
  @JoinColumn({ name: 'parentId' })
  parent: Category

  @Column({ nullable: true })
  parentId: string

  @OneToMany(() => Category, category => category.parent)
  children: Category[]

  @CreateDateColumn()
  createdAt: Date

  @UpdateDateColumn()
  updatedAt: Date

  // Relations
  @OneToMany(() => Product, product => product.category)
  products: Product[]

  // Computed properties
  get level(): number {
    let level = 0
    let current = this.parent
    while (current) {
      level++
      current = current.parent
    }
    return level
  }

  get isRoot(): boolean {
    return !this.parentId
  }

  get hasChildren(): boolean {
    return this.children && this.children.length > 0
  }
}
