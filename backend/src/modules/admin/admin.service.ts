import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Between } from 'typeorm';
import { User, UserRole } from '../../database/entities/user.entity';
import { Product, ProductStatus } from '../../database/entities/product.entity';
import { Category } from '../../database/entities/category.entity';
import { Order, OrderStatus } from '../../database/entities/order.entity';
import { Payment, PaymentStatus } from '../../database/entities/payment.entity';
import { Shipment, ShipmentStatus } from '../../database/entities/shipment.entity';

export interface DashboardStats {
  totalUsers: number;
  totalProducts: number;
  totalOrders: number;
  totalRevenue: number;
  pendingOrders: number;
  lowStockProducts: number;
  recentOrders: Order[];
  topProducts: Array<{ product: Product; totalSold: number }>;
  monthlyRevenue: Array<{ month: string; revenue: number }>;
  ordersByStatus: Array<{ status: string; count: number }>;
}

export interface InventoryAlert {
  id: string;
  productName: string;
  sku: string;
  currentStock: number;
  minStock: number;
  category: string;
  lastRestocked?: Date;
}

@Injectable()
export class AdminService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,
    @InjectRepository(Product)
    private productRepository: Repository<Product>,
    @InjectRepository(Category)
    private categoryRepository: Repository<Category>,
    @InjectRepository(Order)
    private orderRepository: Repository<Order>,
    @InjectRepository(Payment)
    private paymentRepository: Repository<Payment>,
    @InjectRepository(Shipment)
    private shipmentRepository: Repository<Shipment>,
  ) {}

  async getDashboardStats(): Promise<DashboardStats> {
    const [
      totalUsers,
      totalProducts,
      totalOrders,
      pendingOrders,
      lowStockProducts,
      recentOrders,
      totalRevenue,
    ] = await Promise.all([
      this.userRepository.count({ where: { role: UserRole.CUSTOMER } }),
      this.productRepository.count({ where: { status: ProductStatus.ACTIVE } }),
      this.orderRepository.count(),
      this.orderRepository.count({ where: { status: OrderStatus.PENDING } }),
      this.productRepository.count({ where: { stockQuantity: 5 } }),
      this.orderRepository.find({
        take: 10,
        order: { createdAt: 'DESC' },
        relations: ['user', 'orderItems', 'orderItems.product'],
      }),
      this.calculateTotalRevenue(),
    ]);

    const [topProducts, monthlyRevenue, ordersByStatus] = await Promise.all([
      this.getTopProducts(),
      this.getMonthlyRevenue(),
      this.getOrdersByStatus(),
    ]);

    return {
      totalUsers,
      totalProducts,
      totalOrders,
      totalRevenue,
      pendingOrders,
      lowStockProducts,
      recentOrders,
      topProducts,
      monthlyRevenue,
      ordersByStatus,
    };
  }

  async getInventoryAlerts(): Promise<InventoryAlert[]> {
    const lowStockProducts = await this.productRepository
      .createQueryBuilder('product')
      .leftJoinAndSelect('product.category', 'category')
      .where('product.stockQuantity <= :minStock', { minStock: 10 })
      .andWhere('product.status = :status', { status: ProductStatus.ACTIVE })
      .orderBy('product.stockQuantity', 'ASC')
      .getMany();

    return lowStockProducts.map(product => ({
      id: product.id,
      productName: product.name,
      sku: product.sku,
      currentStock: product.stockQuantity,
      minStock: 10,
      category: product.category?.name || 'Uncategorized',
      lastRestocked: product.updatedAt,
    }));
  }

  async updateProductStock(productId: string, newStock: number): Promise<Product> {
    const product = await this.productRepository.findOne({ where: { id: productId } });
    if (!product) {
      throw new Error('Product not found');
    }

    product.stockQuantity = newStock;
    product.updatedAt = new Date();
    
    return this.productRepository.save(product);
  }

  async bulkUpdatePrices(updates: Array<{ productId: string; priceEur: number; priceXaf: number }>): Promise<void> {
    const updatePromises = updates.map(async ({ productId, priceEur, priceXaf }) => {
      await this.productRepository.update(productId, {
        priceEur,
        priceXaf,
        updatedAt: new Date(),
      });
    });

    await Promise.all(updatePromises);
  }

  async getOrdersForAdmin(
    page: number = 1,
    limit: number = 20,
    status?: OrderStatus,
    startDate?: Date,
    endDate?: Date,
  ) {
    const queryBuilder = this.orderRepository
      .createQueryBuilder('order')
      .leftJoinAndSelect('order.user', 'user')
      .leftJoinAndSelect('order.orderItems', 'orderItems')
      .leftJoinAndSelect('orderItems.product', 'product')
      .leftJoinAndSelect('order.payments', 'payments')
      .leftJoinAndSelect('order.shipments', 'shipments');

    if (status) {
      queryBuilder.andWhere('order.status = :status', { status });
    }

    if (startDate && endDate) {
      queryBuilder.andWhere('order.createdAt BETWEEN :startDate AND :endDate', {
        startDate,
        endDate,
      });
    }

    const [orders, total] = await queryBuilder
      .orderBy('order.createdAt', 'DESC')
      .skip((page - 1) * limit)
      .take(limit)
      .getManyAndCount();

    return {
      orders,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async updateOrderStatus(orderId: string, status: OrderStatus): Promise<Order> {
    const order = await this.orderRepository.findOne({ where: { id: orderId } });
    if (!order) {
      throw new Error('Order not found');
    }

    order.status = status;
    order.updatedAt = new Date();

    return this.orderRepository.save(order);
  }

  async getUsersForAdmin(page: number = 1, limit: number = 20, role?: UserRole) {
    const queryBuilder = this.userRepository.createQueryBuilder('user');

    if (role) {
      queryBuilder.where('user.role = :role', { role });
    }

    const [users, total] = await queryBuilder
      .orderBy('user.createdAt', 'DESC')
      .skip((page - 1) * limit)
      .take(limit)
      .getManyAndCount();

    return {
      users,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  private async calculateTotalRevenue(): Promise<number> {
    const result = await this.paymentRepository
      .createQueryBuilder('payment')
      .select('SUM(payment.amount)', 'total')
      .where('payment.status = :status', { status: PaymentStatus.COMPLETED })
      .getRawOne();

    return parseFloat(result.total) || 0;
  }

  private async getTopProducts(): Promise<Array<{ product: Product; totalSold: number }>> {
    const result = await this.productRepository
      .createQueryBuilder('product')
      .leftJoin('product.orderItems', 'orderItem')
      .leftJoin('orderItem.order', 'order')
      .select('product')
      .addSelect('SUM(orderItem.quantity)', 'totalSold')
      .where('order.status IN (:...statuses)', { 
        statuses: [OrderStatus.DELIVERED, OrderStatus.SHIPPED] 
      })
      .groupBy('product.id')
      .orderBy('totalSold', 'DESC')
      .limit(10)
      .getRawAndEntities();

    return result.entities.map((product, index) => ({
      product,
      totalSold: parseInt(result.raw[index].totalSold) || 0,
    }));
  }

  private async getMonthlyRevenue(): Promise<Array<{ month: string; revenue: number }>> {
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

    const result = await this.paymentRepository
      .createQueryBuilder('payment')
      .select("DATE_TRUNC('month', payment.createdAt)", 'month')
      .addSelect('SUM(payment.amount)', 'revenue')
      .where('payment.status = :status', { status: PaymentStatus.COMPLETED })
      .andWhere('payment.createdAt >= :startDate', { startDate: sixMonthsAgo })
      .groupBy("DATE_TRUNC('month', payment.createdAt)")
      .orderBy('month', 'ASC')
      .getRawMany();

    return result.map(row => ({
      month: new Date(row.month).toLocaleDateString('fr-FR', { 
        year: 'numeric', 
        month: 'long' 
      }),
      revenue: parseFloat(row.revenue) || 0,
    }));
  }

  private async getOrdersByStatus(): Promise<Array<{ status: string; count: number }>> {
    const result = await this.orderRepository
      .createQueryBuilder('order')
      .select('order.status', 'status')
      .addSelect('COUNT(*)', 'count')
      .groupBy('order.status')
      .getRawMany();

    return result.map(row => ({
      status: row.status,
      count: parseInt(row.count),
    }));
  }
}
