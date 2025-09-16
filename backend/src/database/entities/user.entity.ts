import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, OneToMany } from 'typeorm'
import { Order } from './order.entity'

export enum UserRole {
  CUSTOMER = 'customer',
  ADMIN = 'admin',
  MODERATOR = 'moderator'
}

@Entity('users')
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string

  @Column({ unique: true })
  email: string

  @Column()
  password: string

  @Column()
  firstName: string

  @Column()
  lastName: string

  @Column({ nullable: true })
  phone: string

  @Column({ type: 'enum', enum: UserRole, default: UserRole.CUSTOMER })
  role: UserRole

  @Column({ default: true })
  isActive: boolean

  @Column({ default: false })
  emailVerified: boolean

  @Column({ nullable: true })
  emailVerificationToken: string

  @Column({ nullable: true })
  passwordResetToken: string

  @Column({ nullable: true })
  passwordResetExpires: Date

  // Address information
  @Column({ nullable: true })
  address: string

  @Column({ nullable: true })
  city: string

  @Column({ nullable: true })
  region: string

  @Column({ nullable: true })
  postalCode: string

  @Column({ default: 'CM' })
  country: string

  // Preferences
  @Column({ default: 'fr' })
  preferredLanguage: string

  @Column({ default: 'XAF' })
  preferredCurrency: string

  @CreateDateColumn()
  createdAt: Date

  @UpdateDateColumn()
  updatedAt: Date

  // Relations
  @OneToMany(() => Order, (order: Order) => order.user)
  orders: Order[]
}
