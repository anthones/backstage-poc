import {
  createFrontendPlugin,
  createRouteRef,
  PageBlueprint,
} from '@backstage/frontend-plugin-api';
import AssignmentIcon from '@material-ui/icons/Assignment';

const rootRouteRef = createRouteRef();

export const deliveryPlugin = createFrontendPlugin({
  pluginId: 'delivery',
  routes: { root: rootRouteRef },
  extensions: [
    PageBlueprint.make({
      params: {
        path: '/delivery',
        title: 'Jira & delivery',
        icon: <AssignmentIcon />,
        routeRef: rootRouteRef,
        noHeader: true,
        loader: () => import('./DeliveryPage').then(m => <m.DeliveryPage />),
      },
    }),
  ],
});
