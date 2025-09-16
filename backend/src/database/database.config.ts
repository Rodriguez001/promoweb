import { TypeOrmModuleOptions } from '@nestjs/typeorm'
import { ConfigService } from '@nestjs/config'
import { User } from './entities/user.entity'
import { Product } from './entities/product.entity'
import { Category } from './entities/category.entity'
import { Order } from './entities/order.entity'
import { OrderItem } from './entities/order-item.entity'
import { Payment } from './entities/payment.entity'
import { Shipment } from './entities/shipment.entity'

export const getDatabaseConfig = (configService: ConfigService): TypeOrmModuleOptions => ({
  type: 'postgres',
  host: configService.get('DB_HOST', 'localhost'),
  port: configService.get('DB_PORT', 5432),
  username: configService.get('DB_USERNAME', 'postgres'),
  password: configService.get('DB_PASSWORD', 'password'),
  database: configService.get('DB_NAME', 'promoweb_africa'),
  entities: [User, Product, Category, Order, OrderItem, Payment, Shipment],
  synchronize: configService.get('NODE_ENV') !== 'production',
  logging: configService.get('NODE_ENV') === 'development',
  ssl: configService.get('NODE_ENV') === 'production' ? { rejectUnauthorized: false } : false,
  migrations: ['dist/database/migrations/*.js'],
  migrationsTableName: 'migrations',
  migrationsRun: false,
})
