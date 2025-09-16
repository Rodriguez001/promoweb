import { Controller, Get, Post, Body, Param, ParseUUIDPipe, UseGuards } from '@nestjs/common'
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger'
import { AuthGuard } from '@nestjs/passport'
import { PaymentsService, CreatePaymentDto, ProcessMobileMoneyDto } from './payments.service'
import { Payment, PaymentMethod, PaymentType } from '../../database/entities/payment.entity'

@ApiTags('payments')
@Controller('payments')
export class PaymentsController {
  constructor(private readonly paymentsService: PaymentsService) {}

  @Post()
  @ApiOperation({ summary: 'Create a new payment' })
  @ApiResponse({ status: 201, description: 'Payment created successfully' })
  @ApiResponse({ status: 400, description: 'Invalid payment data' })
  async create(@Body() createPaymentDto: CreatePaymentDto): Promise<Payment> {
    return this.paymentsService.create(createPaymentDto)
  }

  @Post('mobile-money')
  @ApiOperation({ summary: 'Process mobile money payment' })
  @ApiResponse({ status: 201, description: 'Mobile money payment processed' })
  @ApiResponse({ status: 400, description: 'Payment processing failed' })
  async processMobileMoney(@Body() processMobileMoneyDto: ProcessMobileMoneyDto): Promise<Payment> {
    return this.paymentsService.processMobileMoney(processMobileMoneyDto)
  }

  @Post('card')
  @ApiOperation({ summary: 'Process card payment' })
  @ApiResponse({ status: 201, description: 'Card payment processed' })
  @ApiResponse({ status: 400, description: 'Payment processing failed' })
  async processCard(
    @Body('orderId') orderId: string,
    @Body('amount') amount: number,
    @Body('type') type: PaymentType,
    @Body('cardToken') cardToken: string,
  ): Promise<Payment> {
    return this.paymentsService.processCardPayment(orderId, amount, type, cardToken)
  }

  @Get()
  @UseGuards(AuthGuard('jwt'))
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get all payments' })
  @ApiResponse({ status: 200, description: 'Payments retrieved successfully' })
  async findAll(): Promise<Payment[]> {
    return this.paymentsService.findAll()
  }

  @Get('stats')
  @UseGuards(AuthGuard('jwt'))
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get payment statistics' })
  @ApiResponse({ status: 200, description: 'Payment statistics retrieved successfully' })
  async getStats() {
    return this.paymentsService.getPaymentStats()
  }

  @Get('order/:orderId')
  @ApiOperation({ summary: 'Get payments by order ID' })
  @ApiResponse({ status: 200, description: 'Order payments retrieved successfully' })
  async findByOrder(@Param('orderId', ParseUUIDPipe) orderId: string): Promise<Payment[]> {
    return this.paymentsService.findByOrder(orderId)
  }

  @Get('transaction/:transactionId')
  @ApiOperation({ summary: 'Get payment by transaction ID' })
  @ApiResponse({ status: 200, description: 'Payment retrieved successfully' })
  @ApiResponse({ status: 404, description: 'Payment not found' })
  async findByTransactionId(@Param('transactionId') transactionId: string): Promise<Payment> {
    return this.paymentsService.findByTransactionId(transactionId)
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get payment by ID' })
  @ApiResponse({ status: 200, description: 'Payment retrieved successfully' })
  @ApiResponse({ status: 404, description: 'Payment not found' })
  async findOne(@Param('id', ParseUUIDPipe) id: string): Promise<Payment> {
    return this.paymentsService.findOne(id)
  }

  @Post(':id/refund')
  @UseGuards(AuthGuard('jwt'))
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Refund payment' })
  @ApiResponse({ status: 201, description: 'Payment refunded successfully' })
  @ApiResponse({ status: 400, description: 'Cannot refund payment' })
  async refund(
    @Param('id', ParseUUIDPipe) id: string,
    @Body('amount') amount?: number,
  ): Promise<Payment> {
    return this.paymentsService.refund(id, amount)
  }
}
