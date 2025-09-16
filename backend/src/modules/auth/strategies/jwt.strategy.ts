import { Injectable, UnauthorizedException } from '@nestjs/common'
import { PassportStrategy } from '@nestjs/passport'
import { ExtractJwt, Strategy } from 'passport-jwt'
import { ConfigService } from '@nestjs/config'
import { UsersService } from '../../users/users.service'
import { User } from '../../../database/entities/user.entity'

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(
    private configService: ConfigService,
    private usersService: UsersService,
  ) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: configService.get<string>('JWT_SECRET', 'promoweb-africa-secret-key'),
    })
  }

  async validate(payload: any): Promise<User> {
    const user = await this.usersService.findOne(payload.sub)
    
    if (!user || !user.isActive) {
      throw new UnauthorizedException()
    }
    
    return user
  }
}
