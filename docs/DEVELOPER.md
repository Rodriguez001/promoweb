# 👨‍💻 Guide Développeur - PromoWeb Africa

## 📋 Table des Matières

- [Prérequis](#prérequis)
- [Installation](#installation)
- [Architecture](#architecture)
- [Développement Backend](#développement-backend)
- [Développement Frontend](#développement-frontend)
- [Base de Données](#base-de-données)
- [Tests](#tests)
- [Débogage](#débogage)
- [Standards de Code](#standards-de-code)
- [API Documentation](#api-documentation)

## 🛠️ Prérequis

### Outils Requis
- **Docker Desktop** 4.20+
- **Docker Compose** v2.0+
- **Git** 2.30+
- **VS Code** (recommandé) avec extensions:
  - Python
  - Docker
  - REST Client
  - Thunder Client

### Outils de Développement (Optionnel)
- **Python** 3.11+
- **Node.js** 18+
- **PostgreSQL** 15+ (pour développement local)

## 🚀 Installation

### 1. Clone du Repository
```bash
git clone https://github.com/promoweb-africa/promoweb.git
cd promoweb
```

### 2. Configuration Environnement
```bash
# Copier le template d'environnement
cp .env.example .env

# Configurer les variables (voir section Variables d'Environnement)
nano .env
```

### 3. Démarrage avec Docker
```bash
# Linux/Mac
chmod +x scripts/start.sh
./scripts/start.sh

# Windows
scripts\start.bat
```

### 4. Vérification Installation
```bash
# Vérifier les services
docker-compose ps

# Tester l'API
curl http://localhost:8000/health

# Accéder à la documentation
open http://localhost:8000/docs
```

## 🏗️ Architecture

### Structure du Projet
```
promoweb/
├── 🌐 frontend/               # Application Next.js
│   ├── src/
│   │   ├── app/              # App Router (Next.js 14)
│   │   ├── components/       # Composants réutilisables
│   │   ├── hooks/            # Hooks personnalisés
│   │   ├── lib/              # Utilitaires et configurations
│   │   └── types/            # Types TypeScript
│   ├── public/               # Assets statiques
│   └── package.json
│
├── 🔧 backend/                # API FastAPI
│   ├── app/
│   │   ├── core/            # Configuration et utilitaires
│   │   ├── models/          # Modèles SQLAlchemy
│   │   ├── schemas/         # Schémas Pydantic
│   │   ├── api/             # Endpoints API
│   │   ├── services/        # Logique métier
│   │   └── main.py          # Point d'entrée
│   ├── alembic/             # Migrations DB
│   ├── tests/               # Tests unitaires
│   └── requirements.txt
│
├── 🐳 docker/                 # Configurations Docker
├── 📋 docs/                   # Documentation
├── 🗄️ database/              # Scripts SQL
└── 🚀 scripts/               # Scripts utilitaires
```

### Architecture Backend (FastAPI)

#### 🔒 Core Layer
- **Configuration** (`app/core/config.py`)
- **Base de données** (`app/core/database.py`)
- **Redis/Cache** (`app/core/redis.py`)
- **Logging** (`app/core/logging.py`)
- **Middleware** (`app/core/middleware.py`)

#### 📊 Data Layer
- **Modèles SQLAlchemy** (`app/models/`)
  - Relations et contraintes
  - Méthodes métier
  - Indexes de performance
- **Schémas Pydantic** (`app/schemas/`)
  - Validation d'entrée
  - Sérialisation de sortie
  - Documentation automatique

#### 🌐 API Layer
- **Endpoints REST** (`app/api/v1/endpoints/`)
- **Dépendances** (`app/api/dependencies.py`)
- **Authentification JWT**
- **Rate Limiting**

#### ⚙️ Service Layer
- **Authentification** (`app/services/auth.py`)
- **Paiements** (`app/services/payments/`)
- **Emails** (`app/services/email.py`)
- **Analytics** (`app/services/analytics.py`)

## 🔧 Développement Backend

### Configuration de l'environnement de développement

#### 1. Setup avec Docker (Recommandé)
```bash
# Développement avec hot reload
docker-compose -f docker-compose.dev.yml up -d

# Logs en temps réel
docker-compose logs -f backend
```

#### 2. Setup Local (Avancé)
```bash
cd backend

# Environnement virtuel Python
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installation des dépendances
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Variables d'environnement
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://localhost:6379/0"

# Démarrage du serveur
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Structure des Endpoints

#### Conventions de nommage
```python
# Endpoints REST standards
GET    /api/v1/products          # Liste
POST   /api/v1/products          # Création
GET    /api/v1/products/{id}     # Détail
PUT    /api/v1/products/{id}     # Mise à jour complète
PATCH  /api/v1/products/{id}     # Mise à jour partielle
DELETE /api/v1/products/{id}     # Suppression

# Endpoints d'action
POST   /api/v1/products/{id}/activate
POST   /api/v1/orders/{id}/cancel
POST   /api/v1/cart/clear
```

#### Exemple d'endpoint
```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import get_current_user
from app.schemas.product import ProductResponse, ProductCreate

router = APIRouter()

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Créer un nouveau produit.
    
    - **title**: Titre du produit
    - **price_eur**: Prix en EUR
    - **category_id**: ID de la catégorie
    """
    try:
        product = await ProductService.create(product_data)
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Gestion des Erreurs

#### Exceptions personnalisées
```python
# app/core/exceptions.py
class PromoWebException(Exception):
    """Exception de base pour PromoWeb."""
    pass

class ValidationError(PromoWebException):
    """Erreur de validation des données."""
    pass

class NotFoundError(PromoWebException):
    """Ressource non trouvée."""
    pass

class AuthenticationError(PromoWebException):
    """Erreur d'authentification."""
    pass
```

#### Handler d'exceptions
```python
# app/core/exception_handlers.py
@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "error": "ValidationError",
            "message": str(exc),
            "path": str(request.url.path)
        }
    )
```

### Services et Logique Métier

#### Structure d'un service
```python
# app/services/product_service.py
from app.core.database import get_db_context
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

class ProductService:
    @staticmethod
    async def create(product_data: ProductCreate) -> Product:
        async with get_db_context() as db:
            # Validation métier
            if await ProductService.exists_by_sku(product_data.sku):
                raise ValueError("SKU already exists")
            
            # Création
            product = Product(**product_data.dict())
            db.add(product)
            await db.commit()
            await db.refresh(product)
            
            return product
    
    @staticmethod
    async def exists_by_sku(sku: str) -> bool:
        async with get_db_context() as db:
            result = await db.execute(
                select(Product).where(Product.sku == sku)
            )
            return result.scalar_one_or_none() is not None
```

## 🎨 Développement Frontend

### Configuration Next.js 14

#### Structure App Router
```typescript
// src/app/layout.tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr">
      <body className={inter.className}>
        <Providers>
          <Header />
          <main>{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  )
}

// src/app/products/page.tsx
export default async function ProductsPage() {
  const products = await getProducts()
  
  return (
    <div className="container mx-auto py-8">
      <ProductGrid products={products} />
    </div>
  )
}
```

#### Composants Réutilisables
```typescript
// src/components/ui/Button.tsx
import { cn } from "@/lib/utils"
import { VariantProps, cva } from "class-variance-authority"

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium",
  {
    variants: {
      variant: {
        default: "bg-blue-600 text-white hover:bg-blue-700",
        outline: "border border-gray-300 hover:bg-gray-50",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4",
        lg: "h-12 px-6",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
)

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}
```

### Gestion d'État avec Zustand

```typescript
// src/store/cartStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface CartItem {
  id: string
  title: string
  price: number
  quantity: number
}

interface CartStore {
  items: CartItem[]
  addItem: (item: CartItem) => void
  removeItem: (id: string) => void
  updateQuantity: (id: string, quantity: number) => void
  clearCart: () => void
  total: number
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      items: [],
      addItem: (item) =>
        set((state) => {
          const existingItem = state.items.find((i) => i.id === item.id)
          if (existingItem) {
            return {
              items: state.items.map((i) =>
                i.id === item.id
                  ? { ...i, quantity: i.quantity + item.quantity }
                  : i
              ),
            }
          }
          return { items: [...state.items, item] }
        }),
      removeItem: (id) =>
        set((state) => ({
          items: state.items.filter((item) => item.id !== id),
        })),
      updateQuantity: (id, quantity) =>
        set((state) => ({
          items: state.items.map((item) =>
            item.id === id ? { ...item, quantity } : item
          ),
        })),
      clearCart: () => set({ items: [] }),
      get total() {
        return get().items.reduce(
          (sum, item) => sum + item.price * item.quantity,
          0
        )
      },
    }),
    {
      name: 'cart-storage',
    }
  )
)
```

## 🗄️ Base de Données

### Migrations avec Alembic

#### Créer une migration
```bash
# Auto-génération basée sur les modèles
docker-compose exec backend alembic revision --autogenerate -m "Add product reviews table"

# Migration manuelle
docker-compose exec backend alembic revision -m "Add custom indexes"
```

#### Appliquer les migrations
```bash
# Appliquer toutes les migrations
docker-compose exec backend alembic upgrade head

# Appliquer jusqu'à une révision spécifique
docker-compose exec backend alembic upgrade abc123

# Revenir à une révision précédente
docker-compose exec backend alembic downgrade -1
```

#### Structure d'une migration
```python
# alembic/versions/abc123_add_product_reviews.py
def upgrade() -> None:
    op.create_table(
        'product_reviews',
        sa.Column('id', postgresql.UUID(), primary_key=True),
        sa.Column('product_id', postgresql.UUID(), 
                  sa.ForeignKey('products.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(), 
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'))
    )
    
    # Index pour les performances
    op.create_index('idx_product_reviews_product_id', 
                    'product_reviews', ['product_id'])

def downgrade() -> None:
    op.drop_table('product_reviews')
```

### Requêtes Optimisées

#### Eager Loading
```python
# Charger les relations en une seule requête
products = await db.execute(
    select(Product)
    .options(
        selectinload(Product.category),
        selectinload(Product.inventory),
        selectinload(Product.reviews).selectinload(ProductReview.user)
    )
    .where(Product.is_active == True)
)
```

#### Requêtes avec Jointures
```python
# Jointure avec agrégation
query = (
    select(
        Product.id,
        Product.title,
        func.avg(ProductReview.rating).label('avg_rating'),
        func.count(ProductReview.id).label('review_count')
    )
    .outerjoin(ProductReview)
    .group_by(Product.id, Product.title)
    .having(func.count(ProductReview.id) > 5)
)
```

### PostGIS et Géolocalisation

#### Requêtes spatiales
```python
from geoalchemy2 import func as geo_func

# Trouver les livraisons dans un rayon
nearby_deliveries = await db.execute(
    select(Order)
    .where(
        geo_func.ST_DWithin(
            Order.shipping_location,
            geo_func.ST_GeogFromText(f'POINT({lon} {lat})'),
            5000  # 5km radius
        )
    )
)

# Calculer la distance
distance_query = select(
    Order.id,
    geo_func.ST_Distance(
        Order.shipping_location,
        geo_func.ST_GeogFromText(f'POINT({warehouse_lon} {warehouse_lat})')
    ).label('distance_meters')
).where(Order.shipping_location.isnot(None))
```

## 🧪 Tests

### Structure des Tests
```
tests/
├── unit/                 # Tests unitaires
│   ├── test_services/   # Services
│   ├── test_models/     # Modèles
│   └── test_utils/      # Utilitaires
├── integration/         # Tests d'intégration
│   ├── test_api/        # Endpoints API
│   └── test_database/   # Base de données
└── e2e/                 # Tests end-to-end
    └── test_workflows/  # Workflows complets
```

### Tests Unitaires avec pytest
```python
# tests/unit/test_services/test_auth_service.py
import pytest
from app.services.auth import auth_service
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_create_user():
    """Test création d'utilisateur."""
    user_data = UserCreate(
        email="test@example.com",
        password="Test123!",
        confirm_password="Test123!",
        first_name="Test",
        last_name="User"
    )
    
    user = await auth_service.create_user(user_data)
    
    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.is_active is True

@pytest.mark.asyncio
async def test_authenticate_user():
    """Test authentification utilisateur."""
    # Arrange
    email = "test@example.com"
    password = "Test123!"
    
    # Act
    user = await auth_service.authenticate_user(email, password)
    
    # Assert
    assert user is not None
    assert user.email == email
```

### Tests d'API avec FastAPI TestClient
```python
# tests/integration/test_api/test_products.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_products():
    """Test récupération liste produits."""
    response = client.get("/api/v1/products")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

def test_create_product_unauthorized():
    """Test création produit sans authentification."""
    product_data = {
        "title": "Test Product",
        "price_eur": 29.99,
        "category_id": "uuid-here"
    }
    
    response = client.post("/api/v1/products", json=product_data)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_product_authorized(admin_token):
    """Test création produit avec authentification admin."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    product_data = {
        "title": "Test Product",
        "price_eur": 29.99,
        "category_id": "uuid-here"
    }
    
    response = client.post(
        "/api/v1/products", 
        json=product_data, 
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Product"
```

### Fixtures pytest
```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.database import Base, get_db
from app.main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    """Create test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///test.db")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
    
    await engine.dispose()

@pytest.fixture
async def admin_token(db_session):
    """Create admin user and return JWT token."""
    # Create admin user
    # Generate JWT token
    # Return token
    pass
```

## 🐛 Débogage

### Logs Structurés
```python
import logging
from app.core.logging import get_logger

logger = get_logger(__name__)

async def process_payment(payment_id: str):
    logger.info(
        "Processing payment",
        extra={
            "payment_id": payment_id,
            "user_id": current_user.id,
            "amount": payment.amount
        }
    )
    
    try:
        result = await payment_gateway.process(payment)
        logger.info("Payment processed successfully", extra={
            "payment_id": payment_id,
            "gateway_transaction_id": result.transaction_id
        })
    except PaymentError as e:
        logger.error(
            "Payment processing failed",
            extra={
                "payment_id": payment_id,
                "error": str(e),
                "gateway_response": e.gateway_response
            },
            exc_info=True
        )
```

### Debugging avec VS Code
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000"
            ],
            "cwd": "${workspaceFolder}/backend",
            "env": {
                "DATABASE_URL": "postgresql://...",
                "DEBUG": "true"
            },
            "console": "integratedTerminal"
        }
    ]
}
```

### Profiling Performance
```python
import cProfile
import pstats
from functools import wraps

def profile_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        
        result = await func(*args, **kwargs)
        
        pr.disable()
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 functions
        
        return result
    return wrapper

@router.get("/products")
@profile_endpoint  # En développement seulement
async def get_products():
    # Logic here
    pass
```

## 📏 Standards de Code

### Python (Backend)

#### Formatting avec Black
```bash
# Installation
pip install black isort flake8

# Formatting
black .
isort .
flake8 .
```

#### Configuration
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3

[tool.flake8]
max-line-length = 100
extend-ignore = E203, W503
```

#### Type Hints
```python
from typing import Optional, List, Dict, Union
from pydantic import BaseModel

async def get_products(
    category_id: Optional[str] = None,
    limit: int = 20
) -> List[Product]:
    """Get products with optional filtering."""
    pass

class ProductService:
    @staticmethod
    async def calculate_price(
        base_price: float, 
        discount: Optional[float] = None
    ) -> Dict[str, Union[float, str]]:
        """Calculate final product price."""
        pass
```

### TypeScript (Frontend)

#### Configuration ESLint + Prettier
```json
// .eslintrc.json
{
  "extends": [
    "next/core-web-vitals",
    "@typescript-eslint/recommended",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn"
  }
}

// prettier.config.js
module.exports = {
  semi: false,
  singleQuote: true,
  tabWidth: 2,
  trailingComma: 'es5',
  printWidth: 80,
}
```

#### Conventions de nommage
```typescript
// PascalCase pour les composants
export function ProductCard({ product }: ProductCardProps): JSX.Element {
  return <div>{product.title}</div>
}

// camelCase pour les fonctions
export const calculateTotalPrice = (items: CartItem[]): number => {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0)
}

// SCREAMING_SNAKE_CASE pour les constantes
export const API_BASE_URL = 'http://localhost:8000'
export const MAX_ITEMS_PER_PAGE = 50

// kebab-case pour les fichiers
// product-card.tsx, user-profile.tsx
```

### Documentation du Code

#### Docstrings Python
```python
async def create_order(
    user_id: str, 
    items: List[OrderItemCreate],
    shipping_address: AddressCreate
) -> Order:
    """
    Créer une nouvelle commande.
    
    Args:
        user_id: ID de l'utilisateur
        items: Liste des articles à commander
        shipping_address: Adresse de livraison
        
    Returns:
        Order: La commande créée
        
    Raises:
        ValidationError: Si les données sont invalides
        InsufficientStockError: Si stock insuffisant
        
    Example:
        >>> order = await create_order(
        ...     user_id="123",
        ...     items=[OrderItemCreate(product_id="456", quantity=2)],
        ...     shipping_address=AddressCreate(...)
        ... )
        >>> print(order.order_number)
        PW20241215001
    """
```

#### JSDoc TypeScript
```typescript
/**
 * Calculate shipping cost based on weight and destination
 * 
 * @param weight - Package weight in kg
 * @param destination - Shipping destination code
 * @param options - Additional shipping options
 * @returns Shipping cost calculation result
 * 
 * @example
 * ```typescript
 * const cost = calculateShippingCost(2.5, 'DLA', { express: true })
 * console.log(cost.totalCost) // 5000
 * ```
 */
export function calculateShippingCost(
  weight: number,
  destination: string,
  options: ShippingOptions = {}
): ShippingCostResult {
  // Implementation
}
```

## 📚 API Documentation

### OpenAPI avec FastAPI

La documentation API est générée automatiquement et disponible à :
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Exemples de Requêtes

#### Authentification
```bash
# Inscription
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'

# Connexion
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### Produits
```bash
# Liste des produits
curl "http://localhost:8000/api/v1/products?page=1&per_page=10"

# Recherche de produits
curl "http://localhost:8000/api/v1/products/search?q=iphone&category_id=electronics"

# Détail d'un produit
curl "http://localhost:8000/api/v1/products/550e8400-e29b-41d4-a716-446655440000"
```

#### Panier
```bash
# Ajouter au panier
curl -X POST "http://localhost:8000/api/v1/cart/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "550e8400-e29b-41d4-a716-446655440000",
    "quantity": 2
  }'

# Voir le panier
curl "http://localhost:8000/api/v1/cart" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🆘 Support

### Ressources
- 📧 **Email**: dev@promoweb.cm
- 💬 **Slack**: #promoweb-dev
- 📖 **Wiki**: https://github.com/promoweb-africa/promoweb/wiki

### Contribution
1. Fork le repository
2. Créer une branche feature (`git checkout -b feature/amazing-feature`)
3. Commit les changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

### Issues
Utilisez les templates d'issues pour :
- 🐛 **Bug reports**
- ✨ **Feature requests**  
- 📖 **Documentation improvements**
- ❓ **Questions**
