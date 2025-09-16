import { Injectable, UnauthorizedException, ConflictException } from '@nestjs/common'
import { JwtService } from '@nestjs/jwt'
import { UsersService, CreateUserDto } from '../users/users.service'
import { User } from '../../database/entities/user.entity'
import * as bcrypt from 'bcryptjs'

export interface LoginDto {
  email: string
  password: string
}

export interface RegisterDto extends CreateUserDto {}

export interface AuthResponse {
  access_token: string
  user: Omit<User, 'password'>
}

@Injectable()
export class AuthService {
  constructor(
    private usersService: UsersService,
    private jwtService: JwtService,
  ) {}

  async validateUser(email: string, password: string): Promise<User | null> {
    const user = await this.usersService.findByEmail(email)
    
    if (user && await this.usersService.validatePassword(user, password)) {
      return user
    }
    
    return null
  }

  async login(user: User): Promise<AuthResponse> {
    const payload = { 
      email: user.email, 
      sub: user.id, 
      role: user.role 
    }

    const { password, ...userWithoutPassword } = user

    return {
      access_token: this.jwtService.sign(payload),
      user: userWithoutPassword,
    }
  }

  async register(registerDto: RegisterDto): Promise<AuthResponse> {
    try {
      const user = await this.usersService.create(registerDto)
      return this.login(user)
    } catch (error) {
      if (error instanceof ConflictException) {
        throw error
      }
      throw new Error('Registration failed')
    }
  }

  async validateToken(token: string): Promise<User | null> {
    try {
      const payload = this.jwtService.verify(token)
      const user = await this.usersService.findOne(payload.sub)
      return user
    } catch {
      return null
    }
  }

  async refreshToken(user: User): Promise<AuthResponse> {
    return this.login(user)
  }

  async requestPasswordReset(email: string): Promise<void> {
    const user = await this.usersService.findByEmail(email)
    if (!user) {
      // Don't reveal if email exists or not
      return
    }

    // Generate reset token (in production, use crypto.randomBytes)
    const resetToken = Math.random().toString(36).substring(2, 15)
    const resetExpires = new Date(Date.now() + 3600000) // 1 hour

    // In a real implementation, you would:
    // 1. Save the reset token to the user
    // 2. Send email with reset link
    // For now, we'll just log it
    console.log(`Password reset token for ${email}: ${resetToken}`)
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    // In a real implementation, you would:
    // 1. Find user by reset token
    // 2. Check if token is not expired
    // 3. Update password
    // 4. Clear reset token
    
    // For now, this is a placeholder
    throw new Error('Password reset not implemented yet')
  }
}
