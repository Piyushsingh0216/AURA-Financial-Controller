import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

// Derive stable particle positions from their record IDs. This keeps the data
// core deterministic across React renders and avoids random state shifts when
// a newly uploaded batch refreshes the node list.
function seededUnit(seed) {
  let hash = 2166136261;
  for (let index = 0; index < seed.length; index += 1) {
    hash ^= seed.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) / 4294967296;
}

function positionForNode(id) {
  const key = String(id);
  const radius = 2.8 + seededUnit(`${key}:radius`) * 0.8;
  const theta = seededUnit(`${key}:theta`) * Math.PI * 2;
  const phi = seededUnit(`${key}:phi`) * Math.PI * 2;

  return [
    radius * Math.sin(theta) * Math.cos(phi),
    radius * Math.sin(theta) * Math.sin(phi),
    radius * Math.cos(theta),
  ];
}

function ParticleNodes({ totalCount = 150, exceptions = [], isFocused, activeId, riskLevel, onNodeClick }) {
  const meshRef = useRef();
  
  // Map strictly 1:1 with real data
  const particles = useMemo(() => {
    const temp = [];
    
    // 1. Create specific, clickable nodes for actual exceptions
    exceptions.forEach((exc) => {
      temp.push({ 
        id: exc.bank_stmt_id,
        isException: true,
        pos: positionForNode(exc.bank_stmt_id),
        baseColor: '#FFB800' // Amber
      });
    });

    // 2. Create standard cyan nodes for the remaining successful matches
    const remainingCount = Math.max(0, totalCount - exceptions.length);
    for (let i = 0; i < remainingCount; i++) {
      temp.push({ 
        id: `match-${i}`,
        isException: false,
        pos: positionForNode(`match-${i}`),
        baseColor: '#00F0FF' // Cyan
      });
    }
    return temp;
  }, [totalCount, exceptions]);

  useFrame((state, delta) => {
    if (meshRef.current) {
      const targetSpeed = isFocused ? 0.02 : 0.15;
      meshRef.current.rotation.y += delta * targetSpeed;
      meshRef.current.rotation.x += delta * (isFocused ? 0.01 : 0.05);
      
      const targetZoom = isFocused ? 4.5 : 6;
      state.camera.position.z = THREE.MathUtils.lerp(state.camera.position.z, targetZoom, 0.05);
    }
  });

  return (
    <group ref={meshRef}>
      {particles.map((p) => {
        const isActiveTarget = isFocused && activeId === p.id;
        
        // Handle dynamic coloring for the selected node
        let nodeColor = p.baseColor;
        if (isActiveTarget) {
          if (riskLevel === 'LOW') nodeColor = '#00FF85';
          else if (riskLevel === 'HIGH') nodeColor = '#FF3366';
          else nodeColor = '#FFB800'; 
        }

        const nodeSize = isActiveTarget ? 0.2 : (p.isException ? 0.08 : 0.05);
        const emissiveInt = isActiveTarget ? 4 : 2;

        return (
          <group key={p.id} position={p.pos}>
            <mesh 
              onClick={(e) => {
                if (p.isException) {
                  e.stopPropagation(); // Prevent canvas background click
                  onNodeClick(p.id);
                }
              }}
              onPointerOver={() => {
                if (p.isException) document.body.style.cursor = 'pointer';
              }}
              onPointerOut={() => {
                if (p.isException) document.body.style.cursor = 'auto';
              }}
            >
              <sphereGeometry args={[nodeSize, 16, 16]} />
              <meshStandardMaterial color={nodeColor} emissive={nodeColor} emissiveIntensity={emissiveInt} />
            </mesh>
            
            {/* Deploy the scanning ring strictly on the active data node */}
            {isActiveTarget && (
              <mesh>
                <ringGeometry args={[0.3, 0.35, 32]} />
                <meshBasicMaterial color={nodeColor} transparent opacity={0.6} side={THREE.DoubleSide} />
              </mesh>
            )}
          </group>
        );
      })}
      
      {/* Core Wireframe */}
      <mesh>
        <sphereGeometry args={[1.5, 24, 24]} />
        <meshBasicMaterial color="#00F0FF" wireframe transparent opacity={0.12} />
      </mesh>
    </group>
  );
}

export default function DataCore3D({ isFocused, activeId, riskLevel, onReset, totalCount, exceptions, onNodeClick }) {
  let borderColor = 'border-aura-border';
  let textColor = 'text-aura-cyan/80';
  let statusText = "3D Data Core // Real-Time Ledger Node Map";
  let shadow = '';

  if (isFocused) {
    if (riskLevel === 'LOW') {
      borderColor = 'border-aura-emerald';
      textColor = 'text-aura-emerald';
      statusText = "RISK ASSESSED // LOW EXPOSURE";
      shadow = 'shadow-[0_0_30px_rgba(0,255,133,0.15)]';
    } else if (riskLevel === 'HIGH') {
      borderColor = 'border-aura-red';
      textColor = 'text-aura-red';
      statusText = "CRITICAL ANOMALY // MANUAL OVERRIDE REQUIRED";
      shadow = 'shadow-[0_0_30px_rgba(255,51,102,0.2)]';
    } else {
      borderColor = 'border-aura-amber';
      textColor = 'text-aura-amber';
      statusText = "THREAT LOCKED // ISOLATING ANOMALY";
      shadow = 'shadow-[0_0_30px_rgba(255,184,0,0.15)]';
    }
  }

  return (
    <div className={`w-full h-72 relative rounded-xl border transition-all duration-500 bg-aura-panel/40 backdrop-blur-md overflow-hidden ${borderColor} ${shadow}`}>
      <div className={`absolute top-3 left-4 z-10 text-xs tracking-widest uppercase font-mono transition-colors duration-500 ${textColor}`}>
        {statusText}
      </div>
      
      {isFocused && (
        <button 
          onClick={onReset}
          className="absolute top-3 right-4 z-20 text-[9px] tracking-widest uppercase font-mono text-slate-300 bg-slate-800/80 px-2.5 py-1.5 rounded border border-slate-600 hover:bg-slate-700 hover:text-white transition"
        >
          [ CLICK TO RELEASE ]
        </button>
      )}

      <Canvas camera={{ position: [0, 0, 6], fov: 45 }} onPointerMissed={isFocused ? onReset : null}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1.5} />
        
        <Float speed={isFocused ? 0.2 : 2} rotationIntensity={isFocused ? 0.1 : 1} floatIntensity={isFocused ? 0.1 : 1}>
          <ParticleNodes 
            isFocused={isFocused} 
            activeId={activeId} 
            riskLevel={riskLevel} 
            totalCount={totalCount}
            exceptions={exceptions}
            onNodeClick={onNodeClick}
          />
        </Float>
        
        <OrbitControls enableZoom={false} enablePan={false} autoRotate={!isFocused} autoRotateSpeed={1.0} />
      </Canvas>
    </div>
  );
}
