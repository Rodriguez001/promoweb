# 🛍️ PromoWeb Africa - E-commerce Platform

**Plateforme e-commerce premium** spécialisée dans les produits européens de parapharmacie, beauté, bien-être, et livres à destination des consommateurs camerounais.

[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd promoweb

# Setup development environment
chmod +x setup-dev.sh
./setup-dev.sh

# Start the application
docker-compose up
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Admin Panel: http://localhost:5050

## Fonctionnalités Principales

### E-commerce Complet
- **Catalogue produits** avec synchronisation Google Merchant Center
- **Système d'acompte** (30% minimum) avec paiement échelonné
- **Livraison géolocalisée** avec calcul automatique des frais
- **Multi-devises** (EUR/XAF) avec taux de change en temps réel

### Paiements Intégrés
- **Mobile Money**: Orange Money & MTN Mobile Money
- **Cartes bancaires**: Stripe (Visa, Mastercard)
- **Paiement à la livraison** pour certaines zones

### Expérience Utilisateur
- **Interface responsive** optimisée mobile-first
- **Recherche avancée** avec filtres intelligents
- **Panier persistant** multi-sessions
- **Suivi commandes** en temps réel

### Analytics & Admin
- **Dashboard administrateur** complet
- **Analytics e-commerce** détaillées
- **Gestion des stocks** automatisée
- **Rapports de vente** exportables

## Technologies

### Frontend
- **Next.js 14** - Framework React avec App Router
- **TypeScript** - Typage statique
- **Tailwind CSS** - Framework CSS utilitaire
- **Radix UI** - Composants accessibles
- **React Hook Form** - Gestion des formulaires
- **Zustand** - État global léger

### Backend
- **FastAPI** - Framework Python moderne et rapide
- **SQLAlchemy 2.0** - ORM avec support async
- **PostgreSQL + PostGIS** - Base géospatiale
- **Redis** - Cache haute performance
- **Alembic** - Migrations de base de données
- **Celery** - Tâches asynchrones

### Infrastructure
- **Docker & Docker Compose** - Conteneurisation
- **Nginx** - Proxy inverse et load balancer
- **pgAdmin** - Interface d'administration PostgreSQL
- **Monitoring** - Logs structurés et métriques
- **Système d'acompte** configurable

### Livraison
- **Suivi en temps réel** via APIs DHL/transporteurs
- **Calcul automatique** des frais selon poids/volume

## 🎯 Public Cible

- **Démographie**: Consommateurs urbains 25-45 ans, classe moyenne connectée
- **Localisation**: Douala, Yaoundé principalement
- **Intérêts**: Produits européens de qualité (beauté, bien-être, livres)

## 🏗️ Architecture

```
promoweb-africa/
├── frontend/          # Next.js application
├── backend/           # NestJS API
├── database/          # PostgreSQL schemas & migrations
├── docs/             # Documentation
└── docker/           # Docker configuration
```

## 🚦 Démarrage Rapide

```bash
# Installation des dépendances
npm run install:all

# Développement
npm run dev

# Production
npm run build
npm start
```

## 📋 Fonctionnalités Principales

### ✅ Catalogue Produit
- Affichage optimisé avec images HD
- Filtres avancés (marque, catégorie, prix, ISBN/EAN)
- Promotions et ventes flash
- Recherche intelligente

### ✅ Commandes & Paiement
- Calcul automatique acompte + solde
- Codes promo et réductions
- Paiement Mobile Money + CB
- Notifications automatisées

### ✅ Livraison
- Frais automatisés selon poids/volume
- Livraison domicile ou point relais
- Suivi temps réel des colis

### ✅ Administration
- Gestion stocks avec synchronisation automatique
- Interface commandes et paiements
- Tableau de bord KPI
- Conversion EUR → XAF en temps réel

## 🌍 Conformité

- ❌ Exclusion produits sur prescription
- ✅ Conformité RGPD
- ✅ Sécurité SSL/TLS
- ✅ Réglementations douanières locales

## 📱 Support

- **Bilingue**: Français/Anglais
- **Responsive**: Mobile, tablette, desktop
- **Accessibilité**: Conforme WCAG 2.1

---

*Développé pour simplifier l'accès aux produits européens de qualité au Cameroun*