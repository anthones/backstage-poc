import {
  createFrontendPlugin,
  PageBlueprint,
} from '@backstage/frontend-plugin-api';
import AccountTreeIcon from '@material-ui/icons/AccountTree';

export const demoPlugin = createFrontendPlugin({
  pluginId: 'activation-demo',
  extensions: [
    PageBlueprint.make({
      params: {
        path: '/demo',
        title: 'Engineering handbook',
        icon: <AccountTreeIcon />,
        noHeader: true,
        loader: () => import('./DemoPage').then(m => <m.DemoPage />),
      },
    }),
  ],
});
