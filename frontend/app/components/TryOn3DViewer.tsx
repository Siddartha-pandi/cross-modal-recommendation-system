'use client';

import { useState, useRef, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, Html } from '@react-three/drei';
import { Button } from './ui/button';
import { Download, RotateCcw, ZoomIn, ZoomOut, User } from 'lucide-react';
import * as THREE from 'three';

// Avatar model component
function AvatarModel({ gender = 'female', clothingUrl = null }: { gender: 'male' | 'female', clothingUrl?: string | null }) {
  const avatarRef = useRef<THREE.Group>(null);
  
  // In production, you would load actual GLB models
  // For now, using simple geometric shapes as placeholder
  
  return (
    <group ref={avatarRef}>
      {/* Head */}
      <mesh position={[0, 1.6, 0]}>
        <sphereGeometry args={[0.15, 32, 32]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>
      
      {/* Body */}
      <mesh position={[0, 0.9, 0]}>
        <cylinderGeometry args={[0.25, 0.3, 1.2, 32]} />
        <meshStandardMaterial color={gender === 'male' ? '#4a90e2' : '#e91e63'} />
      </mesh>
      
      {/* Arms */}
      <mesh position={[-0.4, 1.0, 0]} rotation={[0, 0, 0.3]}>
        <cylinderGeometry args={[0.08, 0.08, 0.8, 16]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>
      <mesh position={[0.4, 1.0, 0]} rotation={[0, 0, -0.3]}>
        <cylinderGeometry args={[0.08, 0.08, 0.8, 16]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>
      
      {/* Legs */}
      <mesh position={[-0.15, 0.0, 0]}>
        <cylinderGeometry args={[0.1, 0.1, 0.8, 16]} />
        <meshStandardMaterial color="#2c3e50" />
      </mesh>
      <mesh position={[0.15, 0.0, 0]}>
        <cylinderGeometry args={[0.1, 0.1, 0.8, 16]} />
        <meshStandardMaterial color="#2c3e50" />
      </mesh>
      
      {/* Clothing overlay (if provided) */}
      {clothingUrl && (
        <mesh position={[0, 0.9, 0.05]}>
          <cylinderGeometry args={[0.26, 0.31, 1.2, 32]} />
          <meshStandardMaterial 
            color="#ffffff" 
            transparent 
            opacity={0.8}
            roughness={0.5}
          />
        </mesh>
      )}
    </group>
  );
}

// Loading fallback
function Loader() {
  return (
    <Html center>
      <div className="bg-white p-4 rounded-lg shadow-lg">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
        <p className="mt-2 text-sm text-gray-600">Loading 3D Model...</p>
      </div>
    </Html>
  );
}

interface TryOn3DViewerProps {
  product?: {
    id: string;
    title: string;
    image_url: string;
    category?: string;
  };
}

export default function TryOn3DViewer({ product }: TryOn3DViewerProps) {
  const [gender, setGender] = useState<'male' | 'female'>('female');
  const [zoom, setZoom] = useState(1);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const handleScreenshot = () => {
    if (canvasRef.current) {
      const canvas = canvasRef.current;
      const link = document.createElement('a');
      link.download = `tryon-${product?.id || 'avatar'}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    }
  };

  const handleReset = () => {
    setZoom(1);
  };

  return (
    <div className="w-full h-full flex flex-col bg-gradient-to-br from-purple-50 to-pink-50">
      {/* Header */}
      <div className="p-4 bg-white shadow-sm border-b">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Virtual Try-On Room</h2>
            {product && (
              <p className="text-sm text-gray-600 mt-1">{product.title}</p>
            )}
          </div>
          
          {/* Avatar Selection */}
          <div className="flex gap-2">
            <Button
              variant={gender === 'female' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setGender('female')}
            >
              <User className="w-4 h-4 mr-1" />
              Female
            </Button>
            <Button
              variant={gender === 'male' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setGender('male')}
            >
              <User className="w-4 h-4 mr-1" />
              Male
            </Button>
          </div>
        </div>
      </div>

      {/* 3D Canvas */}
      <div className="flex-1 relative">
        <Canvas
          ref={canvasRef}
          shadows
          camera={{ position: [0, 1.5, 3], fov: 50 }}
          gl={{ preserveDrawingBuffer: true }}
        >
          <Suspense fallback={<Loader />}>
            {/* Lighting */}
            <ambientLight intensity={0.5} />
            <directionalLight 
              position={[5, 5, 5]} 
              intensity={1} 
              castShadow
              shadow-mapSize-width={1024}
              shadow-mapSize-height={1024}
            />
            <pointLight position={[-5, 5, -5]} intensity={0.5} />
            
            {/* Environment */}
            <Environment preset="studio" />
            
            {/* Avatar */}
            <AvatarModel 
              gender={gender} 
              clothingUrl={product?.image_url}
            />
            
            {/* Floor */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.5, 0]} receiveShadow>
              <planeGeometry args={[10, 10]} />
              <shadowMaterial opacity={0.2} />
            </mesh>
            
            {/* Controls */}
            <OrbitControls 
              enableZoom={true}
              enablePan={false}
              minDistance={2}
              maxDistance={5}
              minPolarAngle={Math.PI / 4}
              maxPolarAngle={Math.PI / 2}
            />
          </Suspense>
        </Canvas>

        {/* Instructions Overlay */}
        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm p-3 rounded-lg shadow-lg">
          <p className="text-xs text-gray-600 font-medium mb-1">Controls:</p>
          <ul className="text-xs text-gray-500 space-y-1">
            <li>• Drag to rotate</li>
            <li>• Scroll to zoom</li>
            <li>• Choose avatar gender</li>
          </ul>
        </div>
      </div>

      {/* Bottom Controls */}
      <div className="p-4 bg-white border-t flex items-center justify-between">
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setZoom(Math.min(zoom + 0.2, 2))}
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setZoom(Math.max(zoom - 0.2, 0.5))}
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
          >
            <RotateCcw className="w-4 h-4 mr-1" />
            Reset
          </Button>
        </div>

        <Button
          onClick={handleScreenshot}
          className="bg-purple-600 hover:bg-purple-700"
        >
          <Download className="w-4 h-4 mr-2" />
          Save Screenshot
        </Button>
      </div>
    </div>
  );
}

