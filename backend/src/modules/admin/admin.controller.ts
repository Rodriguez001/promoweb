import { Controller, Get, Post, Put, Body, Param, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth, ApiQuery } from '@nestjs/swagger';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { RolesGuard } from '../auth/guards/roles.guard';
import { Roles } from '../auth/decorators/roles.decorator';
import { UserRole } from '../../database/entities/user.entity';
import { OrderStatus } from '../../database/entities/order.entity';
import { AdminService, DashboardStats, InventoryAlert } from './admin.service';

@ApiTags('admin')
@ApiBearerAuth()
@Controller('admin')
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles(UserRole.ADMIN)
export class AdminController {
  constructor(private readonly adminService: AdminService) {}

  @Get('dashboard')
  @ApiOperation({ summary: 'Get admin dashboard statistics' })
  @ApiResponse({ status: 200, description: 'Dashboard stats retrieved successfully' })
  async getDashboard(): Promise<DashboardStats> {
    return this.adminService.getDashboardStats();
  }

  @Get('inventory/alerts')
  @ApiOperation({ summary: 'Get inventory alerts for low stock products' })
  @ApiResponse({ status: 200, description: 'Inventory alerts retrieved successfully' })
  async getInventoryAlerts(): Promise<InventoryAlert[]> {
    return this.adminService.getInventoryAlerts();
  }

  @Put('inventory/:productId/stock')
  @ApiOperation({ summary: 'Update product stock quantity' })
  @ApiResponse({ status: 200, description: 'Stock updated successfully' })
  async updateProductStock(
    @Param('productId') productId: string,
    @Body('stock') stock: number,
  ) {
    return this.adminService.updateProductStock(productId, stock);
  }

  @Post('inventory/bulk-update-prices')
  @ApiOperation({ summary: 'Bulk update product prices' })
  @ApiResponse({ status: 200, description: 'Prices updated successfully' })
  async bulkUpdatePrices(
    @Body() updates: Array<{ productId: string; priceEur: number; priceXaf: number }>,
  ) {
    await this.adminService.bulkUpdatePrices(updates);
    return { message: 'Prices updated successfully' };
  }

  @Get('orders')
  @ApiOperation({ summary: 'Get orders for admin management' })
  @ApiQuery({ name: 'page', required: false, type: Number })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiQuery({ name: 'status', required: false, enum: OrderStatus })
  @ApiQuery({ name: 'startDate', required: false, type: String })
  @ApiQuery({ name: 'endDate', required: false, type: String })
  @ApiResponse({ status: 200, description: 'Orders retrieved successfully' })
  async getOrders(
    @Query('page') page: number = 1,
    @Query('limit') limit: number = 20,
    @Query('status') status?: OrderStatus,
    @Query('startDate') startDate?: string,
    @Query('endDate') endDate?: string,
  ) {
    const startDateObj = startDate ? new Date(startDate) : undefined;
    const endDateObj = endDate ? new Date(endDate) : undefined;
    
    return this.adminService.getOrdersForAdmin(
      page,
      limit,
      status,
      startDateObj,
      endDateObj,
    );
  }

  @Put('orders/:orderId/status')
  @ApiOperation({ summary: 'Update order status' })
  @ApiResponse({ status: 200, description: 'Order status updated successfully' })
  async updateOrderStatus(
    @Param('orderId') orderId: string,
    @Body('status') status: OrderStatus,
  ) {
    return this.adminService.updateOrderStatus(orderId, status);
  }

  @Get('users')
  @ApiOperation({ summary: 'Get users for admin management' })
  @ApiQuery({ name: 'page', required: false, type: Number })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiQuery({ name: 'role', required: false, enum: UserRole })
  @ApiResponse({ status: 200, description: 'Users retrieved successfully' })
  async getUsers(
    @Query('page') page: number = 1,
    @Query('limit') limit: number = 20,
    @Query('role') role?: UserRole,
  ) {
    return this.adminService.getUsersForAdmin(page, limit, role);
  }
}
