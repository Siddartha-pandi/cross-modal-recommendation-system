'use client';

import ProductDetailPage from '../../components/ProductDetailPage';
import { useParams } from 'next/navigation';

export default function ProductPage() {
  const params = useParams();
  const productId = params.id as string;
  
  return <ProductDetailPage productId={productId} />;
}
