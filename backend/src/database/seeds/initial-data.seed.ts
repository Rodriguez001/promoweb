import { DataSource } from 'typeorm'
import * as bcrypt from 'bcryptjs'
import { User, UserRole } from '../entities/user.entity'
import { Category } from '../entities/category.entity'
import { Product, ProductStatus } from '../entities/product.entity'

export async function seedInitialData(dataSource: DataSource) {
  console.log('🌱 Seeding initial data...')

  // Create admin user
  const userRepository = dataSource.getRepository(User)
  const adminExists = await userRepository.findOne({ where: { email: 'admin@promoweb-africa.com' } })
  
  if (!adminExists) {
    const hashedPassword = await bcrypt.hash('admin123', 12)
    const admin = userRepository.create({
      email: 'admin@promoweb-africa.com',
      password: hashedPassword,
      firstName: 'Admin',
      lastName: 'PromoWeb',
      role: UserRole.ADMIN,
      isActive: true,
      emailVerified: true,
      city: 'Douala',
      region: 'Littoral',
      country: 'CM',
    })
    await userRepository.save(admin)
    console.log('✅ Admin user created')
  }

  // Create categories
  const categoryRepository = dataSource.getRepository(Category)
  const categories = [
    {
      name: 'Parapharmacie',
      slug: 'parapharmacie',
      description: 'Produits de santé et hygiène européens',
      icon: '🏥',
      color: 'from-blue-500 to-cyan-500',
      isFeatured: true,
      sortOrder: 1,
    },
    {
      name: 'Beauté',
      slug: 'beaute',
      description: 'Cosmétiques et soins de beauté européens',
      icon: '💄',
      color: 'from-pink-500 to-rose-500',
      isFeatured: true,
      sortOrder: 2,
    },
    {
      name: 'Bien-être',
      slug: 'bien-etre',
      description: 'Compléments alimentaires et vitamines',
      icon: '🧘',
      color: 'from-green-500 to-emerald-500',
      isFeatured: true,
      sortOrder: 3,
    },
    {
      name: 'Livres',
      slug: 'livres',
      description: 'Livres éducatifs et de développement personnel',
      icon: '📚',
      color: 'from-purple-500 to-indigo-500',
      isFeatured: true,
      sortOrder: 4,
    },
  ]

  for (const categoryData of categories) {
    const exists = await categoryRepository.findOne({ where: { slug: categoryData.slug } })
    if (!exists) {
      const category = categoryRepository.create(categoryData)
      await categoryRepository.save(category)
      console.log(`✅ Category "${categoryData.name}" created`)
    }
  }

  // Create sample products
  const productRepository = dataSource.getRepository(Product)
  const beautyCategory = await categoryRepository.findOne({ where: { slug: 'beaute' } })
  const parapharmacieCategory = await categoryRepository.findOne({ where: { slug: 'parapharmacie' } })
  const wellnessCategory = await categoryRepository.findOne({ where: { slug: 'bien-etre' } })
  const booksCategory = await categoryRepository.findOne({ where: { slug: 'livres' } })

  const sampleProducts = [
    {
      name: 'Crème Hydratante Bio L\'Occitane',
      description: 'Crème hydratante enrichie en beurre de karité pour tous types de peaux',
      shortDescription: 'Hydratation intense 24h',
      brand: 'L\'Occitane',
      sku: 'LOC-CREME-001',
      priceEur: 25.90,
      priceXaf: 17000,
      originalPriceXaf: 20000,
      discountPercentage: 15,
      stockQuantity: 50,
      weight: 0.15,
      categoryId: beautyCategory?.id,
      status: ProductStatus.ACTIVE,
      isFeatured: true,
      isNew: true,
      tags: ['bio', 'hydratant', 'karité'],
      averageRating: 4.8,
      reviewCount: 124,
    },
    {
      name: 'Vitamine D3 + K2 Solgar',
      description: 'Complément alimentaire combinant vitamine D3 et K2 pour la santé osseuse',
      shortDescription: 'Santé osseuse optimale',
      brand: 'Solgar',
      sku: 'SOL-VIT-D3K2',
      priceEur: 19.50,
      priceXaf: 12800,
      stockQuantity: 30,
      weight: 0.08,
      categoryId: wellnessCategory?.id,
      status: ProductStatus.ACTIVE,
      isFeatured: true,
      tags: ['vitamine', 'os', 'immunité'],
      averageRating: 4.9,
      reviewCount: 89,
    },
    {
      name: 'Shampoing Anti-Chute Klorane',
      description: 'Shampoing fortifiant à base de quinine et vitamines B pour cheveux fragiles',
      shortDescription: 'Fortifie et stimule la croissance',
      brand: 'Klorane',
      sku: 'KLO-SHAM-001',
      priceEur: 13.90,
      priceXaf: 8900,
      originalPriceXaf: 11200,
      discountPercentage: 21,
      stockQuantity: 25,
      weight: 0.4,
      categoryId: parapharmacieCategory?.id,
      status: ProductStatus.ACTIVE,
      tags: ['cheveux', 'anti-chute', 'quinine'],
      averageRating: 4.6,
      reviewCount: 156,
    },
    {
      name: 'Le Petit Prince - Antoine de Saint-Exupéry',
      description: 'Édition française du célèbre conte philosophique',
      shortDescription: 'Conte philosophique intemporel',
      brand: 'Gallimard',
      sku: 'GAL-PETIT-PRINCE',
      isbn: '9782070408504',
      priceEur: 6.90,
      priceXaf: 4500,
      stockQuantity: 15,
      weight: 0.12,
      categoryId: booksCategory?.id,
      status: ProductStatus.ACTIVE,
      tags: ['classique', 'philosophie', 'jeunesse'],
      averageRating: 4.9,
      reviewCount: 203,
    },
  ]

  for (const productData of sampleProducts) {
    const exists = await productRepository.findOne({ where: { sku: productData.sku } })
    if (!exists) {
      const product = productRepository.create(productData)
      await productRepository.save(product)
      console.log(`✅ Product "${productData.name}" created`)
    }
  }

  console.log('🎉 Initial data seeding completed!')
}
