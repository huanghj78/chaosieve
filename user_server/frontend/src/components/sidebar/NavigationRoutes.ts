export interface INavigationRoute {
  name: string
  displayName: string
  meta: { icon: string }
  children?: INavigationRoute[]
}

export default {
  root: {
    name: '/',
    displayName: 'navigationRoutes.home',
  },
  routes: [
    {
      name: 'laboratory',
      displayName: 'menu.laboratory',
      meta: {
        icon: 'vuestic-iconset-dashboard',
      },
    },
    {
      name: 'workflow',
      displayName: 'menu.workflow',
      meta: {
        icon: 'vuestic-iconset-graph',
      },
    },
    {
      name: 'target',
      displayName: 'menu.target',
      meta: {
        icon: 'vuestic-iconset-components',
      },
    },
    {
      name: 'result',
      displayName: 'menu.result',
      meta: {
        icon: 'vuestic-iconset-files',
      },
    }
  ] as INavigationRoute[],
}
