import { readFileSync, realpathSync, existsSync } from 'node:fs';
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
const root=fileURLToPath(new URL('.',import.meta.url)),modules=fileURLToPath(new URL('./node_modules',import.meta.url));
export default defineConfig({ plugins: [react()], resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } }, define: { __TB_VERSION__: JSON.stringify(readFileSync(new URL('../VERSION', import.meta.url), 'utf8').trim()) }, server: { fs:{allow:[root,...(existsSync(modules)?[realpathSync(modules)]:[])]}, proxy: { '/api': { target: process.env.TB_API_URL || 'http://127.0.0.1:18765', changeOrigin: true, configure(proxy) { proxy.on('proxyReq', (request) => { request.removeHeader('origin'); request.removeHeader('sec-fetch-site'); }); } } } }, build: { target: 'es2022' } });
