// Adapted from mqnc/cheapwater, MIT, Mirko Kunze (2024).
// Original index.html and textures retained byte-for-byte beside this adapter.
// Both passes share one camera; upstream updateDrops creates every ripple.
import * as THREE from 'three';
import {createPhotographicRain,rainTerminalSpeed} from '../open-water-rain/photographicRain.js';
import rippleURL from './ripple.png?url';
import waterURL from './water_normal.png?url';
import px from './px.jpg?url';
import nx from './nx.jpg?url';
import py from './py.jpg?url';
import ny from './ny.jpg?url';
import pz from './pz.jpg?url';
import nz from './nz.jpg?url';
const environmentURLs=[px,nx,py,ny,pz,nz];
export function createWaterScene(host){
 const renderer=new THREE.WebGLRenderer({antialias:true, preserveDrawingBuffer:true});
 renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.25));
 renderer.domElement.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none';
 host.append(renderer.domElement);
 const camera=new THREE.PerspectiveCamera(56,1,.1,2500);
 camera.up.set(0,0,1);camera.position.set(0,-26,8);camera.lookAt(0,0,0);camera.updateMatrixWorld();
 let resolveReady,rejectReady;
 const ready=new Promise((resolve,reject)=>{resolveReady=resolve;rejectReady=reject});
 const manager=new THREE.LoadingManager(()=>resolveReady(),undefined,url=>rejectReady(Error('Rain texture unavailable: '+url)));
 let impacts=0,lastImpact=null,emission=0,elapsed=0,destroyed=false;
		let normalScene = new THREE.Scene()
		let gray50 = new THREE.Color(0.5, 0.5, 0.5)
		normalScene.background = gray50

		let squareGeometry = new THREE.PlaneGeometry(3, 3)

		let minusMaterial = new THREE.MeshBasicMaterial({
			color: gray50,
			blending: THREE.CustomBlending,
			blendEquation: THREE.ReverseSubtractEquation,
			blendSrc: THREE.SrcAlphaFactor,
			blendDst: THREE.OneFactor,
			blendEquationAlpha: THREE.AddEquation,
			depthTest: false,
			depthWrite: false,
			transparent: true,
			side: THREE.DoubleSide
		})

		let texture = new THREE.TextureLoader(manager).load(rippleURL)
		let plusMaterial = new THREE.MeshBasicMaterial({
			map: texture,
			blending: THREE.CustomBlending,
			blendEquation: THREE.AddEquation,
			blendSrc: THREE.SrcAlphaFactor,
			blendDst: THREE.OneFactor,
			depthTest: false,
			depthWrite: false,
			transparent: true,
			side: THREE.DoubleSide
		})

		let ripples = []
		let order = 0

		function makeRipple(x, y, strength) {
			let minusSquare = new THREE.Mesh(squareGeometry, minusMaterial.clone())
			normalScene.add(minusSquare)
			minusSquare.renderOrder = order++
			minusSquare.position.set(x, y, 0)
			minusSquare.scale.set(0.1, 0.1, 1)
			minusSquare.material.opacity = strength

			let plusSquare = new THREE.Mesh(squareGeometry, plusMaterial.clone())
			normalScene.add(plusSquare)
			plusSquare.renderOrder = order++
			plusSquare.position.set(x, y, 0)
			plusSquare.scale.set(0.1, 0.1, 1)
			plusSquare.material.opacity = strength

			ripples.push({ minus: minusSquare, plus: plusSquare })
		}

		function updateRipples(dt) {
			for (let ripple of [...ripples]) {
				ripple.minus.scale.x += dt * .55
				ripple.minus.scale.y += dt * .55
				ripple.minus.material.opacity -= dt / 60
				ripple.plus.scale.x += dt * .55
				ripple.plus.scale.y += dt * .55
				ripple.plus.material.opacity -= dt / 60
				if (ripple.minus.material.opacity <= 0) {
					normalScene.remove(ripple.minus)
					normalScene.remove(ripple.plus)
					ripples.splice(ripples.indexOf(ripple), 1)
                    ripple.minus.material.dispose()
                    ripple.plus.material.dispose()
				}
			}
		}

		let normalTarget = new THREE.WebGLRenderTarget(1, 1)
		normalTarget.texture.colorSpace = THREE.NoColorSpace
		let normalTextureUniform = { value: normalTarget.texture }

		let colorScene = new THREE.Scene()
		THREE.ColorManagement.enabled = true

		const pmremGenerator = new THREE.PMREMGenerator(renderer)
		pmremGenerator.compileCubemapShader()

		const cubeLoader = new THREE.CubeTextureLoader(manager)
		const envMap = cubeLoader.load(environmentURLs,
			function (texture) {
                if(destroyed){texture.dispose();return;}
				const pmremTexture = pmremGenerator.fromCubemap(texture).texture
				colorScene.environment = pmremTexture
				colorScene.environmentRotation.set(-Math.PI / 2, 0, Math.PI, "XYZ")
				colorScene.background = new THREE.Color(0x283f50)
				colorScene.backgroundRotation.set(-Math.PI / 2, 0, Math.PI, "XYZ")
			}
		)
		let waterMaterial = new THREE.MeshStandardMaterial({
			color: 0x50778f,
			metalness: 0.82,
			roughness: 0.32,
            emissive: 0x17394c,
            emissiveIntensity: 0.25,
			normalMap: new THREE.TextureLoader(manager).load(waterURL),
			normalMapType: THREE.ObjectSpaceNormalMap,
			side: THREE.DoubleSide
		})
		waterMaterial.normalMap.wrapS = THREE.RepeatWrapping
		waterMaterial.normalMap.wrapT = THREE.RepeatWrapping
		waterMaterial.normalMap.repeat.set(80, 80)

		let timeUniform = { value: 0 }
		let resolutionUniform = { value: new THREE.Vector2(1, 1) }
		let overlaysUniform = { value: 0 }

		waterMaterial.onBeforeCompile = (shader) => {
			shader.uniforms.time = timeUniform
			shader.uniforms.resolution = resolutionUniform
			shader.uniforms.normalDisturbance = normalTextureUniform
			shader.uniforms.overlays = overlaysUniform

			shader.fragmentShader =
				"uniform float time;\n" +
				"uniform vec2 resolution;\n" +
				"uniform sampler2D normalDisturbance;\n" +
				"uniform int overlays;\n" +
				shader.fragmentShader.replace(
					"\t#include <normal_fragment_maps>",
					`
					vec3 disturbanceSum = vec3(0.0, 0.0, 0.0);

					for(int i=0; i<10; i++){
						if(i>=overlays){break;}
						float dir = float(i)/float(overlays) * 6.2831853 + 3.0;
						float cd = cos(dir);
						float sd = sin(dir);
						mat2 rot2d = mat2(cd, -sd, sd, cd);
						mat2 invRot2d = mat2(cd, sd, -sd, cd);
						vec3 noise = texture2D(normalMap, rot2d * vNormalMapUv + vec2(time*0.03, dir)).rgb*2.0-1.0;
						noise.xy = invRot2d * noise.xy;
						disturbanceSum += noise;
					}

					vec3 ripples = texture2D(normalDisturbance, gl_FragCoord.xy / resolution).rgb * 2.0 - 1.0;
					disturbanceSum += 3.0 * ripples;

					#ifdef FLIP_SIDED
						disturbanceSum = -disturbanceSum;
					#endif
					#ifdef DOUBLE_SIDED
						disturbanceSum = disturbanceSum * faceDirection;
					#endif
					normal = normalize(normal + normalMatrix * disturbanceSum);
					`
				)
		}

		let waterPlane = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000), waterMaterial)
		colorScene.add(waterPlane)

		let drops = []
		function makeDrop(x, y, z) {
			let d = new THREE.Object3D()
			d.position.set(x, y, z)
            d.userData.rainSeed = [Math.random(),Math.random(),Math.random(),Math.random()]
			d.userData.vz = -rainTerminalSpeed(d.userData.rainSeed)
			colorScene.add(d)
			drops.push(d)
		}

		function updateDrops(dt) {
			for (let d of [...drops]) {
				d.position.z += d.userData.vz * dt
				if (d.position.z < 0) {
					colorScene.remove(d)
					drops.splice(drops.indexOf(d), 1)
                    makeRipple(d.position.x, d.position.y, .18)
                    impacts++
                    lastImpact = {x: d.position.x, y: d.position.y, z: 0}
				}
			}
		}


 colorScene.background=new THREE.Color(0x283f50);
 colorScene.environmentIntensity=.85;
 colorScene.fog=new THREE.FogExp2(0x283f50,.004);
 colorScene.add(new THREE.HemisphereLight(0xadc4d0,0x34596d,2.1));
 envMap.generateMipmaps=true;envMap.minFilter=THREE.LinearMipmapLinearFilter;
 const opticalRain=createPhotographicRain(envMap);colorScene.add(opticalRain.mesh);
 function step(dt,{rain=true}={}){
  elapsed+=dt;timeUniform.value=elapsed;
  if(rain){emission+=dt*128;while(emission>=1){const depth=Math.random(),distant=depth<.25,foreground=depth>.75,y=distant?35+Math.random()*65:foreground?-23+Math.random()*15:-2+Math.random()*37,x=(Math.random()-.5)*(distant?y*1.5:foreground?20:52);makeDrop(x,y,22);emission--;}}
  updateRipples(dt);updateDrops(dt);
 }
 function draw(){if(destroyed)return;opticalRain.sync(drops,camera,renderer.domElement.height);renderer.setRenderTarget(normalTarget);renderer.render(normalScene,camera);renderer.setRenderTarget(null);renderer.render(colorScene,camera);}
 function resize(width,height){renderer.setSize(width,height,false);normalTarget.setSize(renderer.domElement.width,renderer.domElement.height);resolutionUniform.value.set(renderer.domElement.width,renderer.domElement.height);camera.aspect=width/height;camera.updateProjectionMatrix();draw();}
 function destroy(){destroyed=true;const geometries=new Set(),materials=new Set();for(const scene of [normalScene,colorScene])scene.traverse(node=>{if(node.geometry)geometries.add(node.geometry);if(node.material)materials.add(node.material)});for(const geometry of geometries)geometry.dispose();for(const material of materials)material.dispose();texture.dispose();waterMaterial.normalMap.dispose();envMap.dispose();colorScene.environment?.dispose();pmremGenerator.dispose();normalTarget.dispose();renderer.dispose();renderer.forceContextLoss();renderer.domElement.remove();}
 return {renderer,camera,normalScene,colorScene,opticalRain,ready,step,draw,resize,destroy,makeDrop,makeRipple,updateRipples,updateDrops,get drops(){return drops},get ripples(){return ripples},get impactCount(){return impacts},get lastImpact(){return lastImpact}};
}
