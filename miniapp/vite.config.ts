import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import Components from '@uni-helper/vite-plugin-uni-components'
import { UniUIResolver } from '@uni-helper/vite-plugin-uni-components/resolvers'
import Uni from '@uni-helper/plugin-uni'

export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  plugins: [
    // https://uni-helper.js.org/vite-plugin-uni-components
    Components({
      dts: true,
      resolvers: [UniUIResolver()]
    }),
    // https://uni-helper.js.org/plugin-uni
    Uni(),
  ],
  
})


