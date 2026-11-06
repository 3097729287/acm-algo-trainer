// Open Water (Leonxlnx), MIT. Pinned source and license are retained alongside.
// This adapter uses its original photographic rain optics, not solid meshes.
import * as THREE from 'three';
import upstream from './upstream-rain.js?raw';

const vertexOriginal=upstream.match(/const STREAK_VS = `([\s\S]*?)`;/)[1];
const fragmentOriginal=upstream.match(/const STREAK_FS = SKY_LOOKUP_GLSL \+ `([\s\S]*?)`;/)[1];
// CPU impact positions replace only the upstream free-running wrapped volume.
// Thus the visible drop and the water impact always have the same identity.
const vertexShader='precision highp float;\nprecision highp int;\n'+vertexOriginal
 .replace('layout(location = 0) in vec4 aSeed;','in vec4 aSeed;\nin vec3 aPosition;')
 .replace(/vec3 p = aSeed.xyz \* uBox[\s\S]*?vec3 head = uCamPos \+ rel;/,'vec3 head = aPosition;');
// The existing lake supplies the same sky as a cubemap instead of equirectangular.
// Diameter distribution, exposure coverage, soft profile and sky optics remain
// the upstream calculations. The unrelated random splash layer is not imported.
const fragmentShader='precision highp float;\nprecision highp int;\n'+THREE.ShaderChunk.colorspace_pars_fragment+fragmentOriginal
 .replace('uniform sampler2D uEnv;','uniform samplerCube uEnv;')
 .replace('equirectUv(vec3(0.0, 1.0, 0.0))','vec3(0.0, 1.0, 0.0)')
 .replace('equirectUv(normalize(vec3(vDir.x, 0.35, vDir.z)))','normalize(vec3(vDir.x, 0.35, vDir.z))')
 .replace('oColor = vec4(L * a, a);','oColor = vec4(sRGBTransferOETF(vec4(L, 1.0)).rgb * a, a);');
const sourceToScene=new THREE.Matrix4().set(1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1);
const lambda=4.1*Math.pow(25,-.21);

export function rainTerminalSpeed(seed){
 const u=THREE.MathUtils.euclideanModulo(seed[3]*7.31+seed[0]*3.17,1);
 const diameter=THREE.MathUtils.clamp(-Math.log(1-u*.985)/lambda+.35,.35,5);
 return 9.65-10.3*Math.exp(-.6*diameter);
}

export function createPhotographicRain(environment,{capacity=4096}={}){
 const positions=new Float32Array(capacity*3),seeds=new Float32Array(capacity*4);
 const geometry=new THREE.InstancedBufferGeometry();
 geometry.setIndex([0,1,2,2,1,3]);
 geometry.setAttribute('position',new THREE.BufferAttribute(new Float32Array(12),3));
 geometry.setAttribute('aPosition',new THREE.InstancedBufferAttribute(positions,3).setUsage(THREE.DynamicDrawUsage));
 geometry.setAttribute('aSeed',new THREE.InstancedBufferAttribute(seeds,4).setUsage(THREE.DynamicDrawUsage));
 geometry.instanceCount=0;
 const uniforms={uViewProj:{value:new THREE.Matrix4()},uCamPos:{value:new THREE.Vector3()},uBox:{value:new THREE.Vector3(300,30,300)},uExposure:{value:1/60},uLambda:{value:lambda},uCount:{value:1},uWind:{value:new THREE.Vector2()},uPixelAngle:{value:.001},uEnv:{value:environment},uFlash:{value:new THREE.Vector3()},uGain:{value:600}};
 const material=new THREE.RawShaderMaterial({vertexShader,fragmentShader,uniforms,glslVersion:THREE.GLSL3,side:THREE.DoubleSide,transparent:true,premultipliedAlpha:true,depthTest:true,depthWrite:false,blending:THREE.CustomBlending,blendSrc:THREE.OneFactor,blendDst:THREE.OneMinusSrcAlphaFactor});
 material.name='Open Water photographic rain';
 const mesh=new THREE.Mesh(geometry,material);mesh.name=material.name;mesh.frustumCulled=false;mesh.renderOrder=1;
 function sync(drops,camera,height){
  if(drops.length>capacity)throw Error('Rain optical buffer exceeded');
  for(let i=0;i<drops.length;i++){
   const {position,userData}=drops[i];positions.set([position.x,position.z,position.y],i*3);seeds.set(userData.rainSeed,i*4);
  }
  geometry.instanceCount=drops.length;
  geometry.attributes.aPosition.needsUpdate=true;geometry.attributes.aSeed.needsUpdate=true;
  camera.updateMatrixWorld();uniforms.uViewProj.value.copy(camera.projectionMatrix).multiply(camera.matrixWorldInverse).multiply(sourceToScene);
  uniforms.uCamPos.value.set(camera.position.x,camera.position.z,camera.position.y);
  uniforms.uPixelAngle.value=3*Math.tan(THREE.MathUtils.degToRad(camera.fov)*.5)/Math.max(1,height);
 }
 return {mesh,geometry,material,sync};
}
