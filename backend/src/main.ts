import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { ConfigService } from '@nestjs/config';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const configService = app.get(ConfigService);

  // Global validation pipe
  app.useGlobalPipes(new ValidationPipe({
    whitelist: true,
    forbidNonWhitelisted: true,
    transform: true,
  }));

  // CORS configuration
  app.enableCors({
    origin: configService.get('CORS_ORIGIN', 'http://localhost:3000'),
    credentials: true,
  });

  // API prefix
  const apiPrefix = configService.get('API_PREFIX', 'api/v1');
  app.setGlobalPrefix(apiPrefix);

  // Swagger documentation
  const config = new DocumentBuilder()
    .setTitle('PromoWeb Africa API')
    .setDescription('API for PromoWeb Africa e-commerce platform - European products for Cameroon')
    .setVersion('1.0')
    .addTag('auth', 'Authentication endpoints')
    .addTag('users', 'User management')
    .addTag('products', 'Product catalog')
    .addTag('categories', 'Product categories')
    .addTag('orders', 'Order management')
    .addTag('payments', 'Payment processing')
    .addTag('shipments', 'Shipping and tracking')
    .addBearerAuth()
    .addServer(`http://localhost:${configService.get('PORT', 3001)}/${apiPrefix}`, 'Development server')
    .build();

  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('docs', app, document, {
    customSiteTitle: 'PromoWeb Africa API Documentation',
    customfavIcon: '/favicon.ico',
    customCss: `
      .topbar-wrapper img { content: url('/logo.png'); width: 120px; height: auto; }
      .swagger-ui .topbar { background-color: #1f2937; }
    `,
  });

  const port = configService.get('PORT', 3001);
  await app.listen(port);
  
  console.log(`🚀 PromoWeb Africa API is running on: http://localhost:${port}/${apiPrefix}`);
  console.log(`📚 API Documentation available at: http://localhost:${port}/docs`);
}

bootstrap();
