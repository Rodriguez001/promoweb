# Diagrammes UML - PromoWeb Africa

Documentation complète des diagrammes UML pour la plateforme e-commerce PromoWeb utilisant Next.js 14, FastAPI, PostgreSQL+PostGIS.

## 1. 👥 Diagramme de Cas d'Utilisation (Use Cases)

```mermaid
graph LR
    %% Acteurs
    Client[👤 Client]
    Admin[👨‍💼 Administrateur]
    Visiteur[👁️ Visiteur]
    SystemePaiement[💳 Système Paiement]
    Transporteur[🚚 Transporteur]
    
    %% Cas d'utilisation Client
    subgraph "Gestion Catalogue"
        UC1[Consulter Catalogue]
        UC2[Rechercher Produit]
        UC3[Filtrer par Catégorie]
        UC4[Voir Détails Produit]
    end
    
    subgraph "Gestion Panier"
        UC5[Ajouter au Panier]
        UC6[Modifier Quantité]
        UC7[Supprimer Article]
        UC8[Calculer Total]
    end
    
    subgraph "Gestion Commande"
        UC9[Passer Commande]
        UC10[Choisir Mode Livraison]
        UC11[Effectuer Paiement Partiel]
        UC12[Suivre Commande]
        UC13[Confirmer Réception]
    end
    
    subgraph "Gestion Compte"
        UC14[S'inscrire]
        UC15[Se Connecter]
        UC16[Modifier Profil]
        UC17[Consulter Historique]
    end
    
    %% Cas d'utilisation Admin
    subgraph "Administration"
        UC18[Gérer Produits]
        UC19[Gérer Commandes]
        UC20[Gérer Stock]
        UC21[Configurer Prix]
        UC22[Gérer Promotions]
        UC23[Générer Rapports]
        UC24[Gérer Utilisateurs]
    end
    
    %% Relations
    Client --> UC1
    Client --> UC2
    Client --> UC3
    Client --> UC4
    Client --> UC5
    Client --> UC6
    Client --> UC7
    Client --> UC8
    Client --> UC9
    Client --> UC10
    Client --> UC11
    Client --> UC12
    Client --> UC13
    Client --> UC14
    Client --> UC15
    Client --> UC16
    Client --> UC17
    
    Visiteur --> UC1
    Visiteur --> UC2
    Visiteur --> UC3
    Visiteur --> UC4
    Visiteur --> UC14
    
    Admin --> UC18
    Admin --> UC19
    Admin --> UC20
    Admin --> UC21
    Admin --> UC22
    Admin --> UC23
    Admin --> UC24
    
    UC11 --> SystemePaiement
    UC12 --> Transporteur
```

## 2. 🏗️ Diagramme de Classes Principal

```mermaid
classDiagram
    class User {
        +String id
        +String email
        +String firstName
        +String lastName
        +String phone
        +String address
        +DateTime createdAt
        +DateTime updatedAt
        +Boolean isActive
        +register()
        +login()
        +updateProfile()
        +getOrders()
    }
    
    class Admin {
        +String role
        +Array permissions
        +manageProducts()
        +manageOrders()
        +generateReports()
    }
    
    class Product {
        +String id
        +String title
        +String description
        +String isbn
        +String ean
        +String brand
        +String category
        +Float priceEur
        +Float priceXaf
        +Integer stock
        +Array images
        +Boolean isActive
        +DateTime createdAt
        +calculateFinalPrice()
        +updateStock()
        +applyPromotion()
    }
    
    class Category {
        +String id
        +String name
        +String description
        +String slug
        +Integer sortOrder
        +Boolean isActive
    }
    
    class Cart {
        +String id
        +String userId
        +Array items
        +Float totalAmount
        +DateTime createdAt
        +addItem()
        +removeItem()
        +updateQuantity()
        +calculateTotal()
        +clear()
    }
    
    class CartItem {
        +String productId
        +Integer quantity
        +Float unitPrice
        +Float totalPrice
    }
    
    class Order {
        +String id
        +String userId
        +String status
        +Float totalAmount
        +Float depositAmount
        +Float remainingAmount
        +String shippingAddress
        +String paymentMethod
        +DateTime createdAt
        +DateTime deliveredAt
        +calculateShipping()
        +updateStatus()
        +processPayment()
    }
    
    class OrderItem {
        +String orderId
        +String productId
        +Integer quantity
        +Float unitPrice
        +Float totalPrice
    }
    
    class Payment {
        +String id
        +String orderId
        +String type
        +Float amount
        +String status
        +String gateway
        +String transactionId
        +DateTime createdAt
        +processPayment()
        +refund()
    }
    
    class Shipping {
        +String id
        +String orderId
        +String carrier
        +String trackingNumber
        +String status
        +Float weight
        +Float cost
        +Address deliveryAddress
        +DateTime shippedAt
        +DateTime deliveredAt
        +calculateCost()
        +updateTracking()
    }
    
    class Promotion {
        +String id
        +String name
        +String type
        +Float discount
        +DateTime startDate
        +DateTime endDate
        +Boolean isActive
        +apply()
        +isValid()
    }
    
    class Inventory {
        +String productId
        +Integer quantity
        +Integer reservedQuantity
        +Integer minThreshold
        +DateTime lastUpdated
        +updateStock()
        +reserveStock()
        +releaseStock()
    }
    
    %% Relations
    User ||--o{ Order : places
    User ||--|| Cart : has
    Admin --|> User : extends
    
    Product ||--o{ CartItem : contains
    Product ||--o{ OrderItem : contains
    Product }o--|| Category : belongs_to
    Product ||--o{ Inventory : has
    
    Cart ||--o{ CartItem : contains
    Order ||--o{ OrderItem : contains
    Order ||--o{ Payment : has
    Order ||--|| Shipping : has
    
    Promotion }o--o{ Product : applies_to
```

## 3. 📋 Diagrammes de Séquences

### 3.1. Processus de Commande avec Paiement Partiel

```mermaid
sequenceDiagram
    participant C as Client
    participant F as Frontend (Next.js)
    participant A as API (FastAPI)
    participant DB as PostgreSQL
    participant PM as Payment Gateway
    participant SMS as Service SMS
    
    C->>F: Valider le panier
    F->>A: POST /api/orders/create
    A->>DB: Créer commande (status: pending)
    A->>A: Calculer acompte (30%)
    A-->>F: Commande créée + montant acompte
    
    F->>C: Afficher options paiement
    C->>F: Choisir Orange Money
    F->>A: POST /api/payments/process
    A->>PM: Initier paiement Orange Money
    PM-->>A: Token de paiement
    A-->>F: Redirect URL paiement
    
    F->>PM: Redirect client vers paiement
    C->>PM: Effectuer paiement
    PM->>A: Webhook confirmation paiement
    A->>DB: Mettre à jour payment status
    A->>DB: Mettre à jour order status (partially_paid)
    
    A->>SMS: Envoyer SMS confirmation
    A-->>F: Paiement confirmé
    F->>C: Afficher confirmation commande
    
    Note over A: Processus automatique livraison
    A->>DB: Créer shipping record
    A->>SMS: SMS avec numéro suivi
```

### 3.2. Synchronisation Automatique des Produits

```mermaid
sequenceDiagram
    participant Cron as Cron Job
    participant A as API (FastAPI)
    participant GM as Google Merchant
    parameter FX as Forex API
    participant DB as PostgreSQL
    participant Cache as Redis
    
    Cron->>A: Déclenchement tâche quotidienne
    A->>GM: GET XML feed produits
    GM-->>A: XML data (prix EUR)
    
    A->>FX: GET taux EUR/XAF
    FX-->>A: Taux de change actuel
    
    loop Pour chaque produit
        A->>A: Calculer prix XAF final
        A->>A: Arrondir à 100 XAF près
        A->>DB: Upsert produit
        A->>Cache: Invalider cache produit
    end
    
    A->>A: Générer rapport sync
    A->>DB: Logger résultat sync
    
    Note over A: Notifications admin si erreurs
    alt Si erreurs critiques
        A->>SMS: Alerter admin
    end
```

### 3.3. Recherche Intelligente avec Cache

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant Cache as Redis
    participant DB as PostgreSQL
    participant Search as ElasticSearch
    
    U->>F: Taper recherche "livre python"
    F->>F: Debounce (300ms)
    F->>A: GET /api/search?q="livre python"
    
    A->>Cache: Vérifier cache recherche
    
    alt Cache hit
        Cache-->>A: Résultats cachés
    else Cache miss
        A->>Search: Recherche full-text
        Search->>DB: Query avec ranking
        DB-->>Search: Résultats avec métadonnées
        Search-->>A: Résultats formatés
        A->>Cache: Sauvegarder résultats (TTL: 10min)
    end
    
    A-->>F: JSON résultats + suggestions
    F->>F: Render résultats avec highlighting
    F-->>U: Affichage résultats interactifs
    
    Note over F: Analytics tracking
    F->>A: POST /api/analytics/search
    A->>DB: Logger événement recherche
```

### 3.4. Calcul Frais de Livraison Géospatial

```mermaid
sequenceDiagram
    participant C as Client
    participant F as Frontend
    participant A as API
    participant GEO as PostGIS
    participant SHIP as Shipping API
    
    C->>F: Saisir adresse livraison
    F->>A: POST /api/shipping/calculate
    
    A->>GEO: Géocoder adresse
    GEO-->>A: Coordonnées lat/lng
    
    A->>GEO: Calculer distance depuis entrepôt
    GEO-->>A: Distance en km
    
    A->>A: Calculer poids total commande
    A->>A: Appliquer tarifs par zone/poids
    
    alt Zone urbaine (< 20km)
        A->>A: Tarif standard
    else Zone périphérique (20-50km)
        A->>A: Tarif majoré +50%
    else Zone rurale (> 50km)
        A->>SHIP: API transporteur externe
        SHIP-->>A: Tarif spécial
    end
    
    A-->>F: Coût livraison + délai estimé
    F-->>C: Affichage frais + options
```

## 4. 🔄 Diagramme de Transitions d'États

### 4.1. États d'une Commande

```mermaid
stateDiagram-v2
    [*] --> Pending : Création commande
    
    Pending --> PartiallyPaid : Acompte payé
    Pending --> Cancelled : Annulation client
    
    PartiallyPaid --> Processing : Préparation commande
    PartiallyPaid --> Cancelled : Annulation
    
    Processing --> Shipped : Expédition
    Processing --> Cancelled : Problème stock
    
    Shipped --> InTransit : En cours livraison
    
    InTransit --> Delivered : Livraison réussie
    InTransit --> DeliveryFailed : Échec livraison
    
    Delivered --> PaidFull : Solde payé
    Delivered --> Returned : Retour produit
    
    DeliveryFailed --> InTransit : Nouvelle tentative
    DeliveryFailed --> Returned : Retour entrepôt
    
    PaidFull --> Completed : Commande finalisée
    Returned --> Refunded : Remboursement
    Cancelled --> Refunded : Remboursement
    
    Completed --> [*]
    Refunded --> [*]
    
    note right of PartiallyPaid
        Acompte de 30% payé
        Solde à payer à la livraison
    end note
    
    note right of Delivered
        Client confirme réception
        Déclenchement paiement solde
    end note
```

### 4.2. États d'un Paiement

```mermaid
stateDiagram-v2
    [*] --> Initiated : Demande paiement
    
    Initiated --> Processing : Redirection gateway
    Initiated --> Failed : Erreur technique
    Initiated --> Expired : Timeout session
    
    Processing --> Success : Paiement confirmé
    Processing --> Failed : Paiement rejeté
    Processing --> Pending : En attente validation
    
    Pending --> Success : Validation manuelle
    Pending --> Failed : Rejet manuel
    
    Success --> Refunded : Demande remboursement
    
    Failed --> [*]
    Expired --> [*]
    Success --> [*]
    Refunded --> [*]
    
    note right of Processing
        Orange Money, MTN Money
        ou Stripe en cours
    end note
    
    note right of Success
        Webhook reçu
        Commande mise à jour
    end note
```

## 5. 🎯 Diagramme d'Activités - Processus Complet de Commande

```mermaid
flowchart TD
    Start([Client visite catalogue]) --> Browse[Parcourir produits]
    Browse --> Search{Recherche spécifique?}
    Search -->|Oui| SearchBox[Utiliser barre recherche]
    Search -->|Non| Filter[Appliquer filtres]
    
    SearchBox --> ViewProduct[Voir détails produit]
    Filter --> ViewProduct
    
    ViewProduct --> AddCart{Ajouter au panier?}
    AddCart -->|Oui| CartAdd[Produit ajouté]
    AddCart -->|Non| Browse
    
    CartAdd --> ContinueShopping{Continuer achats?}
    ContinueShopping -->|Oui| Browse
    ContinueShopping -->|Non| ViewCart[Voir panier]
    
    ViewCart --> Login{Client connecté?}
    Login -->|Non| Register[Inscription/Connexion]
    Login -->|Oui| Checkout[Processus commande]
    
    Register --> Checkout
    
    Checkout --> Address[Saisir adresse livraison]
    Address --> CalcShipping[Calculer frais livraison]
    CalcShipping --> PaymentMethod[Choisir mode paiement]
    
    PaymentMethod --> PartialPay[Paiement acompte 30%]
    PartialPay --> PaymentGateway[Redirection gateway]
    PaymentGateway --> PaymentResult{Paiement réussi?}
    
    PaymentResult -->|Non| PaymentFailed[Échec paiement]
    PaymentResult -->|Oui| OrderConfirm[Confirmation commande]
    
    PaymentFailed --> PaymentMethod
    
    OrderConfirm --> SMS1[SMS confirmation]
    SMS1 --> Prepare[Préparation commande]
    Prepare --> Ship[Expédition]
    Ship --> SMS2[SMS numéro suivi]
    SMS2 --> Track[Suivi livraison]
    Track --> Delivery[Livraison]
    Delivery --> PayRemain[Paiement solde]
    PayRemain --> Complete[Commande terminée]
    
    Complete --> End([Fin])
    
    style Start fill:#e1f5fe
    style End fill:#e8f5e8
    style PaymentGateway fill:#fff3e0
    style OrderConfirm fill:#e8f5e8
```

## 6. 🏛️ Diagramme de Composants Architecture

```mermaid
graph TB
    %% Frontend Components
    subgraph "Frontend Layer (Next.js 14)"
        UI[UI Components<br/>Radix UI + Tailwind]
        Pages[Pages & Routing<br/>App Router]
        Store[State Management<br/>React Query + Zustand]
        Auth[Authentication<br/>NextAuth.js]
        Maps[Maps Component<br/>MapLibre GL]
    end
    
    %% API Gateway
    subgraph "API Layer (FastAPI)"
        Router[API Router<br/>FastAPI Routes]
        Middleware[Middleware<br/>Auth + CORS + Rate Limiting]
        Validation[Data Validation<br/>Pydantic v2]
        Auth_API[JWT Authentication<br/>python-jose]
    end
    
    %% Business Logic
    subgraph "Business Logic"
        ProductService[Product Service<br/>Catalogue Management]
        OrderService[Order Service<br/>Order Processing]
        PaymentService[Payment Service<br/>Multi-gateway]
        ShippingService[Shipping Service<br/>Geo Calculation]
        NotificationService[Notification Service<br/>SMS + Email]
    end
    
    %% Data Layer
    subgraph "Data Layer"
        ORM[SQLAlchemy ORM<br/>Models & Relations]
        Migration[Alembic<br/>DB Migrations]
        Spatial[GeoAlchemy2<br/>Spatial Queries]
    end
    
    %% Database
    subgraph "Database Layer"
        PostgreSQL[(PostgreSQL<br/>Primary Database)]
        PostGIS[(PostGIS<br/>Spatial Extension)]
        Redis[(Redis<br/>Cache + Sessions)]
    end
    
    %% External Services
    subgraph "External Services"
        Stripe[Stripe<br/>Card Payments]
        OrangeMoney[Orange Money<br/>Mobile Payment]
        MTN[MTN Mobile Money<br/>Mobile Payment]
        GoogleMerchant[Google Merchant<br/>Product Feed]
        ForexAPI[Exchange Rate API<br/>EUR/XAF Rates]
        SMSGateway[SMS Gateway<br/>Notifications]
        ShippingAPI[Shipping APIs<br/>Tracking Services]
    end
    
    %% Infrastructure
    subgraph "Infrastructure"
        Docker[Docker Compose<br/>Container Orchestration]
        NGINX[NGINX<br/>Reverse Proxy + SSL]
        CloudStorage[Cloud Storage<br/>File Uploads]
        Monitoring[Monitoring<br/>Prometheus + Grafana]
    end
    
    %% Connections
    UI --> Pages
    Pages --> Store
    Pages --> Auth
    Store --> Router
    
    Router --> Middleware
    Middleware --> Validation
    Middleware --> Auth_API
    
    Validation --> ProductService
    Validation --> OrderService
    Validation --> PaymentService
    Validation --> ShippingService
    Validation --> NotificationService
    
    ProductService --> ORM
    OrderService --> ORM
    PaymentService --> ORM
    ShippingService --> Spatial
    
    ORM --> PostgreSQL
    Spatial --> PostGIS
    Store --> Redis
    
    PaymentService --> Stripe
    PaymentService --> OrangeMoney
    PaymentService --> MTN
    ProductService --> GoogleMerchant
    ProductService --> ForexAPI
    NotificationService --> SMSGateway
    ShippingService --> ShippingAPI
    
    Docker --> PostgreSQL
    Docker --> Redis
    Docker --> NGINX
    NGINX --> Router
```

## 7. 📊 Diagramme de Déploiement

```mermaid
graph TB
    %% Client Devices
    subgraph "Client Layer"
        Mobile[📱 Mobile<br/>iOS/Android PWA]
        Desktop[🖥️ Desktop<br/>Web Browser]
        Tablet[📟 Tablet<br/>Responsive UI]
    end
    
    %% CDN & Load Balancer
    subgraph "Edge Layer"
        CDN[🌐 Cloudflare CDN<br/>Static Assets + Cache]
        LB[⚖️ Load Balancer<br/>NGINX + SSL Termination]
    end
    
    %% Application Servers
    subgraph "Application Layer (Cloudways/DigitalOcean)"
        subgraph "Frontend Servers"
            Next1[Next.js Server 1<br/>SSR + Static Generation]
            Next2[Next.js Server 2<br/>SSR + Static Generation]
        end
        
        subgraph "API Servers"
            API1[FastAPI Server 1<br/>Gunicorn + Uvicorn]
            API2[FastAPI Server 2<br/>Gunicorn + Uvicorn]
        end
        
        subgraph "Background Services"
            Celery[Celery Workers<br/>Async Tasks]
            Scheduler[Cron Jobs<br/>Sync & Maintenance]
        end
    end
    
    %% Database Layer
    subgraph "Database Layer"
        Primary[(PostgreSQL Primary<br/>Read/Write)]
        Replica[(PostgreSQL Replica<br/>Read Only)]
        RedisCache[(Redis Cluster<br/>Cache + Sessions)]
    end
    
    %% Storage
    subgraph "Storage Layer"
        FileStorage[📁 S3 Compatible<br/>Images + Files]
        Backup[💾 Automated Backup<br/>Daily DB + Files]
    end
    
    %% External Services
    subgraph "External APIs"
        PaymentGW[💳 Payment Gateways<br/>Stripe + Mobile Money]
        ShippingAPI[🚚 Shipping APIs<br/>Tracking Services]
        SMSAPI[📨 SMS/Email APIs<br/>Notifications]
        DataFeeds[📊 Data Feeds<br/>Google Merchant + Forex]
    end
    
    %% Monitoring
    subgraph "Monitoring & Logs"
        Prometheus[📊 Prometheus<br/>Metrics Collection]
        Grafana[📈 Grafana<br/>Dashboards]
        Loki[📝 Loki<br/>Log Aggregation]
        Sentry[🚨 Sentry<br/>Error Tracking]
    end
    
    %% Connections
    Mobile --> CDN
    Desktop --> CDN
    Tablet --> CDN
    
    CDN --> LB
    LB --> Next1
    LB --> Next2
    
    Next1 --> API1
    Next2 --> API2
    
    API1 --> Primary
    API2 --> Primary
    API1 --> Replica
    API2 --> Replica
    
    API1 --> RedisCache
    API2 --> RedisCache
    
    Celery --> Primary
    Celery --> RedisCache
    Scheduler --> Primary
    
    API1 --> FileStorage
    API2 --> FileStorage
    
    Primary --> Backup
    FileStorage --> Backup
    
    API1 --> PaymentGW
    API2 --> PaymentGW
    API1 --> ShippingAPI
    API2 --> ShippingAPI
    API1 --> SMSAPI
    API2 --> SMSAPI
    Scheduler --> DataFeeds
    
    %% Monitoring connections
    API1 --> Prometheus
    API2 --> Prometheus
    Primary --> Prometheus
    
    Prometheus --> Grafana
    API1 --> Loki
    API2 --> Loki
    Next1 --> Sentry
    Next2 --> Sentry
    API1 --> Sentry
    API2 --> Sentry
    
    %% Styling
    classDef client fill:#e1f5fe,stroke:#01579b
    classDef edge fill:#f3e5f5,stroke:#4a148c
    classDef app fill:#e8f5e8,stroke:#1b5e20
    classDef data fill:#fff3e0,stroke:#e65100
    classDef external fill:#fce4ec,stroke:#880e4f
    classDef monitor fill:#f1f8e9,stroke:#33691e
    
    class Mobile,Desktop,Tablet client
    class CDN,LB edge
    class Next1,Next2,API1,API2,Celery,Scheduler app
    class Primary,Replica,RedisCache,FileStorage,Backup data
    class PaymentGW,ShippingAPI,SMSAPI,DataFeeds external
    class Prometheus,Grafana,Loki,Sentry monitor
```

## 8. 🔐 Diagramme de Sécurité et Authentification

```mermaid
graph TD
    %% User Authentication Flow
    subgraph "Authentication Layer"
        User[👤 User Request]
        JWT[🔑 JWT Token]
        OAuth[🔐 OAuth Providers<br/>Google, Facebook]
        Session[📝 Session Management]
    end
    
    %% API Security
    subgraph "API Security (FastAPI)"
        RateLimit[⏱️ Rate Limiting<br/>Redis-based]
        CORS[🌐 CORS Policy<br/>Origin Validation]
        AuthMiddleware[🛡️ Auth Middleware<br/>JWT Validation]
        Validation[✅ Input Validation<br/>Pydantic v2]
        Sanitization[🧹 Data Sanitization<br/>XSS Protection]
    end
    
    %% Data Security
    subgraph "Data Protection"
        Encryption[🔒 Encryption at Rest<br/>AES-256]
        HashPasswords[# Password Hashing<br/>bcrypt]
        PII[👥 PII Protection<br/>RGPD Compliance]
        Audit[📋 Audit Logging<br/>Security Events]
    end
    
    %% Network Security
    subgraph "Network Security"
        SSL[🔐 SSL/TLS<br/>Certificate]
        Firewall[🔥 Firewall Rules<br/>IP Filtering]
        VPN[🔒 VPN Access<br/>Admin Only]
        DDoS[🛡️ DDoS Protection<br/>Cloudflare]
    end
    
    %% Payment Security
    subgraph "Payment Security"
        PCI[💳 PCI Compliance<br/>Tokenization]
        Webhook[🔗 Webhook Validation<br/>Signature Verification]
        Fraud[🕵️ Fraud Detection<br/>Risk Scoring]
    end
    
    %% Connections
    User --> JWT
    User --> OAuth
    JWT --> Session
    
    Session --> RateLimit
    RateLimit --> CORS
    CORS --> AuthMiddleware
    AuthMiddleware --> Validation
    Validation --> Sanitization
    
    Sanitization --> Encryption
    Sanitization --> HashPasswords
    Encryption --> PII
    HashPasswords --> Audit
    
    SSL --> Firewall
    Firewall --> VPN
    VPN --> DDoS
    
    PCI --> Webhook
    Webhook --> Fraud
```

---

## 📚 Guide d'Utilisation des Diagrammes

### 🎯 Objectifs de la Documentation UML

1. **Vision d'ensemble** : Comprendre l'architecture complète
2. **Communication** : Faciliter les échanges entre équipes
3. **Planification** : Guider le développement étape par étape
4. **Maintenance** : Documenter les processus métier
5. **Formation** : Onboarding des nouveaux développeurs

### 🛠️ Outils Recommandés

- **Mermaid Live Editor** : https://mermaid.live
- **VS Code Extension** : Mermaid Markdown Syntax
- **GitHub/GitLab** : Rendu automatique des diagrammes
- **Draw.io** : Alternative pour diagrammes complexes

### 📋 Checklist d'Implémentation

- [ ] **Use Cases** : Valider avec les stakeholders
- [ ] **Classes** : Implémenter les modèles SQLAlchemy
- [ ] **Séquences** : Développer les endpoints FastAPI
- [ ] **États** : Configurer la machine à états
- [ ] **Activités** : Tester les parcours utilisateur
- [ ] **Composants** : Structurer l'architecture
- [ ] **Déploiement** : Configurer l'infrastructure
- [ ] **Sécurité** : Implémenter les contrôles

### 🔄 Mise à Jour

Ces diagrammes doivent évoluer avec le projet :
- **Révision mensuelle** des cas d'utilisation
- **Mise à jour** des diagrammes de classes après modifications
- **Validation** des séquences lors de nouveaux features
- **Documentation** des changements d'architecture

---

*Dernière mise à jour : Septembre 2024*  
*Stack : Next.js 14, FastAPI, PostgreSQL+PostGIS, Docker*
