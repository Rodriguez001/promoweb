import { Injectable, NotFoundException, ConflictException } from '@nestjs/common'
import { InjectRepository } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { User, UserRole } from '../../database/entities/user.entity'
import * as bcrypt from 'bcryptjs'

export interface CreateUserDto {
  email: string
  password: string
  firstName: string
  lastName: string
  phone?: string
  address?: string
  city?: string
  region?: string
  postalCode?: string
  preferredLanguage?: string
}

export interface UpdateUserDto {
  firstName?: string
  lastName?: string
  phone?: string
  address?: string
  city?: string
  region?: string
  postalCode?: string
  preferredLanguage?: string
  preferredCurrency?: string
}

@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,
  ) {}

  async create(createUserDto: CreateUserDto): Promise<User> {
    const existingUser = await this.userRepository.findOne({
      where: { email: createUserDto.email }
    })

    if (existingUser) {
      throw new ConflictException('User with this email already exists')
    }

    const hashedPassword = await bcrypt.hash(createUserDto.password, 12)

    const user = this.userRepository.create({
      ...createUserDto,
      password: hashedPassword,
    })

    return this.userRepository.save(user)
  }

  async findAll(): Promise<User[]> {
    return this.userRepository.find({
      select: ['id', 'email', 'firstName', 'lastName', 'phone', 'role', 'isActive', 'createdAt'],
      order: { createdAt: 'DESC' }
    })
  }

  async findOne(id: string): Promise<User> {
    const user = await this.userRepository.findOne({
      where: { id },
      select: ['id', 'email', 'firstName', 'lastName', 'phone', 'role', 'isActive', 'address', 'city', 'region', 'postalCode', 'country', 'preferredLanguage', 'preferredCurrency', 'createdAt', 'updatedAt']
    })

    if (!user) {
      throw new NotFoundException(`User with ID ${id} not found`)
    }

    return user
  }

  async findByEmail(email: string): Promise<User | null> {
    return this.userRepository.findOne({
      where: { email }
    })
  }

  async update(id: string, updateUserDto: UpdateUserDto): Promise<User> {
    const user = await this.findOne(id)
    
    Object.assign(user, updateUserDto)
    
    return this.userRepository.save(user)
  }

  async updatePassword(id: string, newPassword: string): Promise<void> {
    const hashedPassword = await bcrypt.hash(newPassword, 12)
    
    await this.userRepository.update(id, {
      password: hashedPassword,
      passwordResetToken: null,
      passwordResetExpires: null,
    })
  }

  async verifyEmail(id: string): Promise<void> {
    await this.userRepository.update(id, {
      emailVerified: true,
      emailVerificationToken: null,
    })
  }

  async deactivate(id: string): Promise<void> {
    await this.userRepository.update(id, { isActive: false })
  }

  async activate(id: string): Promise<void> {
    await this.userRepository.update(id, { isActive: true })
  }

  async updateRole(id: string, role: UserRole): Promise<User> {
    const user = await this.findOne(id)
    user.role = role
    return this.userRepository.save(user)
  }

  async validatePassword(user: User, password: string): Promise<boolean> {
    return bcrypt.compare(password, user.password)
  }

  async getUserStats(): Promise<{
    total: number
    active: number
    customers: number
    admins: number
    recentRegistrations: number
  }> {
    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

    const [total, active, customers, admins, recentRegistrations] = await Promise.all([
      this.userRepository.count(),
      this.userRepository.count({ where: { isActive: true } }),
      this.userRepository.count({ where: { role: UserRole.CUSTOMER } }),
      this.userRepository.count({ where: { role: UserRole.ADMIN } }),
      this.userRepository.count({
        where: {
          createdAt: { $gte: thirtyDaysAgo } as any
        }
      })
    ])

    return { total, active, customers, admins, recentRegistrations }
  }
}
