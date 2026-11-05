import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {fractureCells,clipFracturePolygon,fractureGeometry,createFractureBodies,fractureKineticEnergy,fractureVertices,stepFracture} from '../src/lib/sceneFracturePhysics.js';

const near=(actual,expected,tolerance=1e-7)=>assert(Math.abs(actual-expected)<tolerance,`${actual} != ${expected}`);
const square=[[-5,-5],[5,-5],[5,5],[-5,5]];
const shape=fractureGeometry([square]);
near(shape.area,100);near(shape.cx,0);near(shape.cy,0);near(shape.inertia,100/6);
const seeds=[[1,1],[8,2],[3,6],[9,8],[1,9]],outline=[[0,0],[10,0],[10,10],[0,10]];
const geometries=fractureCells({x:0,y:0,width:10,height:10},seeds).map(cell=>fractureGeometry([clipFracturePolygon(outline,cell.polygon)]));
near(geometries.reduce((sum,p)=>sum+p.area,0),100);
near(geometries.reduce((sum,p)=>sum+p.area*p.cx,0),500);
assert.equal(fractureGeometry([clipFracturePolygon(square,[[20,20],[30,20],[30,30],[20,30]])]),null);

const proof=[];
for(const material of ['glass','ceramic']){
 const options={material,impact:{x:5,y:10},impactSpeed:380,random:()=>.6};
 const bodies=createFractureBodies(geometries,options);
 assert(bodies.some(b=>b.mode==='collapse')&&bodies.some(b=>b.mode==='eject'));
 assert(Math.max(...bodies.filter(b=>b.mode==='collapse').map(b=>Math.hypot(b.vx,b.vy)))<Math.min(...bodies.filter(b=>b.mode==='eject').map(b=>Math.hypot(b.vx,b.vy))));
 const mass=bodies.reduce((sum,b)=>sum+b.mass,0),energy=fractureKineticEnergy(bodies);
 assert(energy<=.5*mass*380**2*(material==='glass'?.24:.32)+1e-6,'Fracturing cannot exceed the available kinetic energy');
 const higher=createFractureBodies(geometries,{...options,impactSpeed:760});
 assert(fractureKineticEnergy(higher)>energy*3.9,'Higher drops provide proportionally more fracture energy');

 // Equal gravitational acceleration and exact ballistic travel, without contact.
 const body=createFractureBodies([shape],options)[0];Object.assign(body,{x:0,y:0,vx:73,vy:-120,spin:0});
 const initialY=body.y,initialVy=body.vy;
 for(let i=0;i<24;i++)stepFracture([body],1/240,{material,gravity:1800,floor:10000});
 near(body.y,initialY+initialVy*.1+.5*1800*.1**2);near(body.vy,initialVy+180);

 // A rotated shard contacts through its edge, never through its centroid.
 const falling=createFractureBodies([shape],options)[0];Object.assign(falling,{x:0,y:0,vx:55,vy:240,angle:.71,spin:2});
 let maximumPenetration=0;
 for(let i=0;i<480;i++){
  stepFracture([falling],1/240,{material,floor:80});
  maximumPenetration=Math.max(maximumPenetration,...fractureVertices(falling).map(p=>p[1]-80));
 }
 assert(maximumPenetration<1e-6);assert(falling.asleep,'Floor friction eventually stops the shard');
 near(falling.vx,0);near(falling.vy,0);near(falling.spin,0);

 // Head-on fragment collisions dissipate kinetic energy with gravity disabled.
 const pair=createFractureBodies([shape,shape],options);
 Object.assign(pair[0],{x:-5.1,y:0,vx:80,vy:0,spin:0});Object.assign(pair[1],{x:5.1,y:0,vx:-80,vy:0,spin:0});
 const before=fractureKineticEnergy(pair);
 stepFracture(pair,1/240,{material,gravity:0,floor:1000});
 assert(fractureKineticEnergy(pair)<=before);assert(pair[0].vx<pair[1].vx,'Fragments separate after collision');
 proof.push({material,energyBudget:true,mixedImpulses:true,higherImpactEnergy:true,ballisticGravity:true,edgeContact:true,maximumPenetration,settled:true,inelasticFragmentCollision:true});
}
const out='../.backups/fracture-physics-20261105';await mkdir(out,{recursive:true});
await writeFile(out+'/model.json',JSON.stringify({ok:true,materialPartitionConserved:true,proof},null,2));
console.log('PASS fracture coverage, mass/inertia, impulse energy budget, mixed collapse/ejection, ballistic gravity, rotating edge contacts, friction, settling and fragment collisions');
