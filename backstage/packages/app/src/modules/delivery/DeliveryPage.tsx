import { useEffect, useState } from 'react';
import { useSearchParams, Link as RouterLink } from 'react-router-dom';
import {
  Content,
  Header,
  Page,
  Progress,
  WarningPanel,
} from '@backstage/core-components';
import {
  discoveryApiRef,
  fetchApiRef,
  useApi,
} from '@backstage/core-plugin-api';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  Link,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@material-ui/core';

type Component = {
  name: string;
  title: string;
  owner: string;
  project: string;
  label: string;
};
type Issue = {
  key: string;
  summary: string;
  status: string;
  type: string;
  links: { key: string; relationship: string }[];
  url: string | null;
  handover: string;
};
type Result = {
  source: string;
  notice: string;
  fetched_at: string;
  issues: Issue[];
  has_more: boolean;
  jql: string;
  component: Component | null;
  browse_url?: string;
};

export function DeliveryPage() {
  const discovery = useApi(discoveryApiRef);
  const fetchApi = useApi(fetchApiRef);
  const [params, setParams] = useSearchParams();
  const source = params.get('source') === 'scenario' ? 'scenario' : 'public';
  const component = source === 'scenario' ? params.get('component') || '' : '';
  const [components, setComponents] = useState<Component[]>([]);
  const [result, setResult] = useState<Result>();
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(undefined);
    setResult(undefined);
    async function load() {
      try {
        const base = `${await discovery.getBaseUrl('proxy')}/jira-poc`;
        const query = new URLSearchParams({
          source,
          ...(component ? { component } : {}),
        });
        const responses = await Promise.all([
          fetchApi.fetch(`${base}/components`),
          fetchApi.fetch(`${base}/issues?${query}`),
        ]);
        const bodies = await Promise.all(responses.map(r => r.json()));
        if (responses.some(r => !r.ok))
          throw new Error(
            bodies.find(b => b.detail)?.detail ||
              'Jira adapter is unavailable. Check the runner and proxy configuration.',
          );
        if (active) {
          setComponents(bodies[0]);
          setResult(bodies[1]);
        }
      } catch (e) {
        if (active)
          setError(
            e instanceof Error ? e.message : 'Could not load Jira issues',
          );
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [source, component, revision, discovery, fetchApi]);

  return (
    <Page themeId="tool">
      <Header
        title="Jira & delivery"
        subtitle="Connect planned work with service context"
      />
      <Content>
        <Box mb={3}>
          <Typography paragraph>
            Read Jira work alongside catalog ownership, API agreements, support
            instructions, and QA handovers.
          </Typography>
          <Box display="flex" flexWrap="wrap" gridGap={16} alignItems="center">
            <FormControl variant="outlined" style={{ minWidth: 280 }}>
              <InputLabel id="source-label">Source</InputLabel>
              <Select
                labelId="source-label"
                label="Source"
                value={source}
                onChange={e => setParams({ source: String(e.target.value) })}
              >
                <MenuItem value="public">
                  Atlassian public Jira · live read-only
                </MenuItem>
                <MenuItem value="scenario">
                  Activation handover · fictional example
                </MenuItem>
              </Select>
            </FormControl>
            {source === 'scenario' && (
              <FormControl variant="outlined" style={{ minWidth: 260 }}>
                <InputLabel id="component-label">Service or website</InputLabel>
                <Select
                  labelId="component-label"
                  label="Service or website"
                  value={component}
                  onChange={e =>
                    setParams({
                      source,
                      ...(e.target.value
                        ? { component: String(e.target.value) }
                        : {}),
                    })
                  }
                >
                  <MenuItem value="">Whole activation journey</MenuItem>
                  {components.map(c => (
                    <MenuItem key={c.name} value={c.name}>
                      {c.title}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            <Button
              variant="outlined"
              onClick={() => setRevision(n => n + 1)}
              disabled={loading}
            >
              Refresh
            </Button>
          </Box>
        </Box>
        {loading && <Progress />}
        {error && <WarningPanel title="Jira is unavailable" message={error} />}
        {result && (
          <>
            <Box mb={2} p={2} component={Paper}>
              <Typography variant="h6">
                {result.source === 'public'
                  ? 'Real connection, public issues'
                  : 'Fictional work linked to our example services'}
              </Typography>
              <Typography paragraph>{result.notice}</Typography>
              <Typography variant="body2">
                Retrieved: {new Date(result.fetched_at).toLocaleString()} ·{' '}
                {result.issues.length} issues shown
                {result.has_more
                  ? ' · limited preview, more exist in Jira'
                  : ''}
              </Typography>
              <Typography variant="body2">
                Query: <code>{result.jql}</code>
              </Typography>
              {result.browse_url && (
                <Link
                  href={result.browse_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open this query in Atlassian Jira ↗
                </Link>
              )}
              {result.component && (
                <Typography>
                  <Link
                    component={RouterLink}
                    to={`/catalog/default/component/${result.component.name}`}
                  >
                    Open {result.component.title} in the catalog
                  </Link>
                  {' · Owner: '}
                  <Link
                    component={RouterLink}
                    to={`/catalog/default/group/${result.component.owner}`}
                  >
                    {result.component.owner}
                  </Link>
                </Typography>
              )}
            </Box>
            <Paper style={{ overflowX: 'auto' }}>
              <Table aria-label="Jira work">
                <TableHead>
                  <TableRow>
                    <TableCell>Issue / work</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Explicit Jira links</TableCell>
                    {source === 'scenario' && (
                      <TableCell>Handover to prepare</TableCell>
                    )}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.issues.map(issue => (
                    <TableRow key={issue.key}>
                      <TableCell>
                        {issue.url ? (
                          <Link
                            href={issue.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {issue.key} ↗
                          </Link>
                        ) : (
                          <strong>{issue.key}</strong>
                        )}
                        <Typography>{issue.summary}</Typography>
                      </TableCell>
                      <TableCell>{issue.status}</TableCell>
                      <TableCell>
                        {issue.links.length
                          ? issue.links.map((l, i) => (
                              <Typography key={i}>
                                {l.relationship} {l.key}
                              </Typography>
                            ))
                          : 'No links returned'}
                      </TableCell>
                      {source === 'scenario' && (
                        <TableCell>{issue.handover}</TableCell>
                      )}
                    </TableRow>
                  ))}
                  {!result.issues.length && (
                    <TableRow>
                      <TableCell colSpan={source === 'scenario' ? 4 : 3}>
                        No matching issues. Check the catalog project and label
                        mapping.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Paper>
            <Box mt={3}>
              <Typography paragraph>
                <strong>For product owners:</strong> connect a requested outcome
                to affected services and teams before agreeing scope or release
                dates.
              </Typography>
              <Typography paragraph>
                <strong>For business analysts:</strong> follow the API and
                domain documentation to agree business rules, acceptance
                examples, and handover evidence with the right owners.
              </Typography>
              <Typography variant="body2">
                Catalog dependencies describe software structure. Jira issue
                links describe recorded work dependencies. Neither automatically
                proves a blocker, an approval, or release readiness. Jira
                remains the place to edit work.
              </Typography>
            </Box>
          </>
        )}
      </Content>
    </Page>
  );
}
