import { createApp } from '@backstage/frontend-defaults';
import catalogPlugin from '@backstage/plugin-catalog/alpha';
import { navModule } from './modules/nav';
import { homeModule } from './modules/home';
import { demoPlugin } from './modules/demo';
import { deliveryPlugin } from './modules/delivery';

export default createApp({
  features: [catalogPlugin, navModule, homeModule, demoPlugin, deliveryPlugin],
});
