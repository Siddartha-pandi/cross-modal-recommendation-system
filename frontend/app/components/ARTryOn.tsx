'use client';

import { useEffect, useRef, useState } from 'react';
import { Button } from './ui/button';
import { Camera, RotateCcw, Share2, Info } from 'lucide-react';

// Declare model-viewer custom element
declare global {
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': any;
    }
  }
}

interface ARTryOnProps {
  product?: {
    id: string;
    title: string;
    category?: string;
    image_url?: string;
  };
}

export default function ARTryOn({ product }: ARTryOnProps) {
  const [modelLoaded, setModelLoaded] = useState(false);
  const [arSupported, setArSupported] = useState(true);
  const modelViewerRef = useRef<any>(null);

  useEffect(() => {
    // Load model-viewer script
    const script = document.createElement('script');
    script.type = 'module';
    script.src = 'https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js';
    document.head.appendChild(script);

    // Check AR support
    if (modelViewerRef.current) {
      modelViewerRef.current.addEventListener('ar-status', (event: any) => {
        if (event.detail.status === 'not-presenting') {
          setArSupported(false);
        }
      });
    }

    return () => {
      document.head.removeChild(script);
    };
  }, []);

  const handleScreenshot = async () => {
    if (modelViewerRef.current) {
      try {
        const screenshot = await modelViewerRef.current.toBlob();
        const url = URL.createObjectURL(screenshot);
        const link = document.createElement('a');
        link.download = `ar-tryon-${product?.id || 'product'}.png`;
        link.href = url;
        link.click();
        URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Screenshot failed:', error);
      }
    }
  };

  const handleReset = () => {
    if (modelViewerRef.current) {
      modelViewerRef.current.resetTurntableRotation();
      modelViewerRef.current.cameraOrbit = '0deg 75deg 105%';
    }
  };

  // Get model URL based on product category
  const getModelUrl = () => {
    // In production, you would fetch actual 3D models
    // For demo, using placeholder GLB models
    const category = product?.category?.toLowerCase() || '';
    
    // Example model URLs (replace with actual models)
    if (category.includes('glasses') || category.includes('sunglasses')) {
      return 'https://modelviewer.dev/shared-assets/models/glTF-Sample-Models/2.0/DamagedHelmet/glTF/DamagedHelmet.gltf';
    } else if (category.includes('hat') || category.includes('cap')) {
      return 'https://modelviewer.dev/shared-assets/models/glTF-Sample-Models/2.0/DamagedHelmet/glTF/DamagedHelmet.gltf';
    } else {
      // Default model
      return 'https://modelviewer.dev/shared-assets/models/Astronaut.glb';
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Header */}
      <div className="p-4 bg-white shadow-sm border-b">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">AR Try-On Experience</h2>
            {product && (
              <p className="text-sm text-gray-600 mt-1">{product.title}</p>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <div className="text-xs text-gray-500 flex items-center gap-1">
              <Info className="w-3 h-3" />
              {arSupported ? 'AR Ready' : 'View Mode'}
            </div>
          </div>
        </div>
      </div>

      {/* Model Viewer */}
      <div className="flex-1 relative">
        <model-viewer
          ref={modelViewerRef}
          src={getModelUrl()}
          alt={product?.title || 'Product 3D Model'}
          ar
          ar-modes="webxr scene-viewer quick-look"
          camera-controls
          auto-rotate
          shadow-intensity="1"
          exposure="1"
          tone-mapping="commerce"
          style={{
            width: '100%',
            height: '100%',
            backgroundColor: 'transparent'
          }}
          onLoad={() => setModelLoaded(true)}
        >
          {/* Loading indicator */}
          {!modelLoaded && (
            <div slot="poster" className="absolute inset-0 flex items-center justify-center bg-white">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto"></div>
                <p className="mt-4 text-sm text-gray-600">Loading 3D Model...</p>
              </div>
            </div>
          )}

          {/* AR Button */}
          <button
            slot="ar-button"
            className="absolute bottom-20 left-1/2 transform -translate-x-1/2 bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-full font-medium shadow-lg flex items-center gap-2 transition-all"
          >
            <Camera className="w-5 h-5" />
            View in AR
          </button>
        </model-viewer>

        {/* Instructions Overlay */}
        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm p-4 rounded-lg shadow-lg max-w-xs">
          <h3 className="font-semibold text-sm text-gray-900 mb-2">How to use AR:</h3>
          <ol className="text-xs text-gray-600 space-y-2">
            <li className="flex gap-2">
              <span className="font-bold text-purple-600">1.</span>
              <span>Click "View in AR" button</span>
            </li>
            <li className="flex gap-2">
              <span className="font-bold text-purple-600">2.</span>
              <span>Point your camera at a flat surface</span>
            </li>
            <li className="flex gap-2">
              <span className="font-bold text-purple-600">3.</span>
              <span>Move around to see the product from all angles</span>
            </li>
            <li className="flex gap-2">
              <span className="font-bold text-purple-600">4.</span>
              <span>Take a screenshot to share with friends</span>
            </li>
          </ol>
          
          {!arSupported && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <p className="text-xs text-amber-600 flex items-center gap-1">
                <Info className="w-3 h-3" />
                AR not available on this device. Using 3D viewer mode.
              </p>
            </div>
          )}
        </div>

        {/* Feature Pills */}
        <div className="absolute top-4 right-4 flex flex-col gap-2">
          <div className="bg-green-500 text-white text-xs px-3 py-1 rounded-full font-medium">
            360° View
          </div>
          <div className="bg-blue-500 text-white text-xs px-3 py-1 rounded-full font-medium">
            Real Scale
          </div>
          <div className="bg-purple-500 text-white text-xs px-3 py-1 rounded-full font-medium">
            Camera Ready
          </div>
        </div>
      </div>

      {/* Bottom Controls */}
      <div className="p-4 bg-white border-t flex items-center justify-between">
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
          >
            <RotateCcw className="w-4 h-4 mr-1" />
            Reset View
          </Button>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleScreenshot}
          >
            <Camera className="w-4 h-4 mr-1" />
            Screenshot
          </Button>
          <Button
            size="sm"
            className="bg-purple-600 hover:bg-purple-700"
          >
            <Share2 className="w-4 h-4 mr-1" />
            Share
          </Button>
        </div>
      </div>

      {/* Device Compatibility Info */}
      <div className="px-4 pb-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-xs text-blue-800">
            <strong>💡 Best Experience:</strong> Use iOS 12+ (Safari) or Android 8+ (Chrome) for full AR capabilities
          </p>
        </div>
      </div>
    </div>
  );
}

