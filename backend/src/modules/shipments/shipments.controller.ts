import { Controller, Get, Post, Body, Patch, Param, ParseUUIDPipe, UseGuards } from '@nestjs/common'
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger'
import { AuthGuard } from '@nestjs/passport'
import { ShipmentsService, CreateShipmentDto, UpdateTrackingDto } from './shipments.service'
import { Shipment, ShipmentStatus } from '../../database/entities/shipment.entity'

@ApiTags('shipments')
@Controller('shipments')
export class ShipmentsController {
  constructor(private readonly shipmentsService: ShipmentsService) {}

  @Post()
  @UseGuards(AuthGuard('jwt'))
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create a new shipment' })
  @ApiResponse({ status: 201, description: 'Shipment created successfully' })
  @ApiResponse({ status: 400, description: 'Invalid shipment data' })
  async create(@Body() createShipmentDto: CreateShipmentDto): Promise<Shipment> {
    return this.shipmentsService.create(createShipmentDto)
  }

  @Get()
  @UseGuards(AuthGuard('jwt'))
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get all shipments' })
  @ApiResponse({ status: 200, description: 'Shipments retrieved successfully' })
  async findAll(): Promise<Shipment[]> {
    return this.shipmentsService.findAll()
  }

  @Get('stats')
  @UseGuards(AuthGuard('jwt'))
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get shipment statistics' })
  @ApiResponse({ status: 200, description: 'Shipment statistics retrieved successfully' })
  async getStats() {
    return this.shipmentsService.getShipmentStats()
  }

  @Get('track/:trackingNumber')
  @ApiOperation({ summary: 'Track shipment by tracking number' })
  @ApiResponse({ status: 200, description: 'Shipment tracking information retrieved' })
  @ApiResponse({ status: 404, description: 'Shipment not found' })
  async track(@Param('trackingNumber') trackingNumber: string): Promise<Shipment> {
    return this.shipmentsService.findByTrackingNumber(trackingNumber)
  }

  @Get('order/:orderId')
  @ApiOperation({ summary: 'Get shipments by order ID' })
  @ApiResponse({ status: 200, description: 'Order shipments retrieved successfully' })
  async findByOrder(@Param('orderId', ParseUUIDPipe) orderId: string): Promise<Shipment[]> {
    return this.shipmentsService.findByOrder(orderId)
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get shipment by ID' })
  @ApiResponse({ status: 200, description: 'Shipment retrieved successfully' })
  @ApiResponse({ status: 404, description: 'Shipment not found' })
  async findOne(@Param('id', ParseUUIDPipe) id: string): Promise<Shipment> {
    return this.shipmentsService.findOne(id)
  }

  @Patch(':id/status')
  @UseGuards(AuthGuard('jwt'))
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update shipment status' })
  @ApiResponse({ status: 200, description: 'Shipment status updated successfully' })
  async updateStatus(
    @Param('id', ParseUUIDPipe) id: string,
    @Body('status') status: ShipmentStatus,
    @Body('description') description?: string,
    @Body('location') location?: string,
  ): Promise<Shipment> {
    return this.shipmentsService.updateStatus(id, status, description, location)
  }

  @Patch(':id/carrier-tracking')
  @UseGuards(AuthGuard('jwt'))
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update carrier tracking number' })
  @ApiResponse({ status: 200, description: 'Carrier tracking updated successfully' })
  async updateCarrierTracking(
    @Param('id', ParseUUIDPipe) id: string,
    @Body('carrierTrackingNumber') carrierTrackingNumber: string,
  ): Promise<Shipment> {
    return this.shipmentsService.updateCarrierTracking(id, carrierTrackingNumber)
  }

  @Post(':id/tracking-event')
  @UseGuards(AuthGuard('jwt'))
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Add tracking event' })
  @ApiResponse({ status: 201, description: 'Tracking event added successfully' })
  async addTrackingEvent(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() updateTrackingDto: UpdateTrackingDto,
  ): Promise<Shipment> {
    return this.shipmentsService.addTrackingEvent(id, updateTrackingDto)
  }

  @Post('simulate/:trackingNumber')
  @ApiOperation({ summary: 'Simulate tracking update (for demo purposes)' })
  @ApiResponse({ status: 200, description: 'Tracking simulation completed' })
  async simulateTracking(@Param('trackingNumber') trackingNumber: string): Promise<Shipment> {
    return this.shipmentsService.simulateTracking(trackingNumber)
  }
}
