// @ts-nocheck - Bypassing React type conflicts with Radix UI components
/**
 * AdminDashboard - Main admin interface for PromoWeb Africa
 * Provides overview of orders, products, and analytics
 */

'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Package,
  ShoppingCart,
  Users,
  CreditCard,
  TrendingUp,
  TrendingDown,
  Eye,
  Edit,
  Trash2,
  Plus,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { formatCurrency, formatDate } from '@/lib/utils';

// Mock data - replace with actual API calls
const mockStats = {
  totalOrders: 1234,
  totalRevenue: 45000000,
  totalProducts: 856,
  totalUsers: 2456,
  ordersGrowth: 12.5,
  revenueGrowth: 8.3,
  productsGrowth: 5.2,
  usersGrowth: 15.7
};

const mockRecentOrders = [
  {
    id: '1',
    orderNumber: 'PMW20240001',
    customerName: 'Jean Dupont',
    status: 'processing',
    total: 125000,
    createdAt: '2024-09-21T10:30:00Z'
  },
  {
    id: '2',
    orderNumber: 'PMW20240002',
    customerName: 'Marie Kouam',
    status: 'shipped',
    total: 89000,
    createdAt: '2024-09-21T09:15:00Z'
  },
  {
    id: '3',
    orderNumber: 'PMW20240003',
    customerName: 'Paul Ngomo',
    status: 'delivered',
    total: 156000,
    createdAt: '2024-09-21T08:45:00Z'
  }
];

const mockTopProducts = [
  {
    id: '1',
    title: 'iPhone 15 Pro Max',
    sales: 45,
    revenue: 2250000,
    stock: 12
  },
  {
    id: '2',
    title: 'Samsung Galaxy S24',
    sales: 38,
    revenue: 1900000,
    stock: 8
  },
  {
    id: '3',
    title: 'MacBook Pro 16"',
    sales: 22,
    revenue: 3300000,
    stock: 5
  }
];

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  growth?: number;
  trend?: 'up' | 'down';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, growth, trend }) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {growth !== undefined && (
          <div className="flex items-center text-xs text-muted-foreground">
            {trend === 'up' ? (
              <TrendingUp className="mr-1 h-3 w-3 text-green-500" />
            ) : (
              <TrendingDown className="mr-1 h-3 w-3 text-red-500" />
            )}
            <span className={trend === 'up' ? 'text-green-500' : 'text-red-500'}>
              {growth > 0 ? '+' : ''}{growth}%
            </span>
            <span className="ml-1">depuis le mois dernier</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const getStatusBadge = (status: string) => {
  const statusMap = {
    pending: { label: 'En attente', variant: 'secondary' as const },
    confirmed: { label: 'Confirmée', variant: 'default' as const },
    processing: { label: 'En traitement', variant: 'default' as const },
    shipped: { label: 'Expédiée', variant: 'default' as const },
    delivered: { label: 'Livrée', variant: 'default' as const },
    cancelled: { label: 'Annulée', variant: 'destructive' as const }
  };

  const statusInfo = statusMap[status as keyof typeof statusMap] || statusMap.pending;
  return <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>;
};

export const AdminDashboard: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('30d');

  // Mock queries - replace with actual API calls
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats', selectedPeriod],
    queryFn: () => Promise.resolve(mockStats),
    staleTime: 5 * 60 * 1000 // 5 minutes
  });

  const { data: recentOrders, isLoading: ordersLoading } = useQuery({
    queryKey: ['admin-recent-orders'],
    queryFn: () => Promise.resolve(mockRecentOrders),
    staleTime: 2 * 60 * 1000 // 2 minutes
  });

  const { data: topProducts, isLoading: productsLoading } = useQuery({
    queryKey: ['admin-top-products'],
    queryFn: () => Promise.resolve(mockTopProducts),
    staleTime: 10 * 60 * 1000 // 10 minutes
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Dashboard Admin</h1>
          <p className="text-muted-foreground">
            Vue d'ensemble de votre boutique PromoWeb Africa
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* @ts-ignore - React 18/19 JSX type compatibility */}
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-40">
              {/* @ts-ignore - React 18/19 JSX type compatibility */}
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">7 derniers jours</SelectItem>
              <SelectItem value="30d">30 derniers jours</SelectItem>
              <SelectItem value="90d">90 derniers jours</SelectItem>
              <SelectItem value="1y">Cette année</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualiser
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Commandes"
          value={stats?.totalOrders.toLocaleString() || '0'}
          icon={<ShoppingCart className="h-4 w-4 text-muted-foreground" />}
          growth={stats?.ordersGrowth}
          trend={stats?.ordersGrowth && stats.ordersGrowth > 0 ? 'up' : 'down'}
        />
        
        <StatCard
          title="Chiffre d'Affaires"
          value={stats ? formatCurrency(stats.totalRevenue) : '0 XAF'}
          icon={<CreditCard className="h-4 w-4 text-muted-foreground" />}
          growth={stats?.revenueGrowth}
          trend={stats?.revenueGrowth && stats.revenueGrowth > 0 ? 'up' : 'down'}
        />
        
        <StatCard
          title="Total Produits"
          value={stats?.totalProducts.toLocaleString() || '0'}
          icon={<Package className="h-4 w-4 text-muted-foreground" />}
          growth={stats?.productsGrowth}
          trend={stats?.productsGrowth && stats.productsGrowth > 0 ? 'up' : 'down'}
        />
        
        <StatCard
          title="Utilisateurs"
          value={stats?.totalUsers.toLocaleString() || '0'}
          icon={<Users className="h-4 w-4 text-muted-foreground" />}
          growth={stats?.usersGrowth}
          trend={stats?.usersGrowth && stats.usersGrowth > 0 ? 'up' : 'down'}
        />
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="orders" className="space-y-4">
        <TabsList>
          <TabsTrigger value="orders">Commandes Récentes</TabsTrigger>
          <TabsTrigger value="products">Produits Top</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Recent Orders Tab */}
        <TabsContent value="orders" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Commandes Récentes</CardTitle>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <Filter className="h-4 w-4 mr-2" />
                  Filtrer
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Exporter
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Numéro</TableHead>
                    <TableHead>Client</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentOrders?.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell className="font-medium">
                        {order.orderNumber}
                      </TableCell>
                      <TableCell>{order.customerName}</TableCell>
                      <TableCell>
                        {getStatusBadge(order.status)}
                      </TableCell>
                      <TableCell>{formatCurrency(order.total)}</TableCell>
                      <TableCell>
                        {formatDate(order.createdAt)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Top Products Tab */}
        <TabsContent value="products" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Produits les Plus Vendus</CardTitle>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Nouveau Produit
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Produit</TableHead>
                    <TableHead>Ventes</TableHead>
                    <TableHead>Revenus</TableHead>
                    <TableHead>Stock</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topProducts?.map((product, index) => (
                    <TableRow key={product.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-muted-foreground">
                            #{index + 1}
                          </span>
                          <span className="font-medium">{product.title}</span>
                        </div>
                      </TableCell>
                      <TableCell>{product.sales} unités</TableCell>
                      <TableCell>{formatCurrency(product.revenue)}</TableCell>
                      <TableCell>
                        <Badge variant={product.stock < 10 ? "destructive" : "secondary"}>
                          {product.stock} en stock
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Évolution des Ventes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center text-muted-foreground">
                  Graphique des ventes (à implémenter)
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Top Catégories</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center text-muted-foreground">
                  Graphique des catégories (à implémenter)
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
