import React, { useEffect, useMemo, useState } from "react";
import { calculateSprintRisk } from "./utils/sprintRiskCalculator";
import { getDashboardTeams, getDashboardSprints, getSprintMetrics, getProjectVelocity, getDeliverySummary, getDeliveryVelocity } from "./services/dashboardService";
import { NavLink, Routes, Route, useLocation, useNavigate } from "react-router-dom";
import {
  Activity, AlertTriangle, BarChart3, Bot, BrainCircuit, CalendarClock,
  CheckCircle2, ChevronDown, ChevronRight, CircleDot, Clock3, Code2,
  Database, Gauge, GitPullRequest, History, Home, KanbanSquare, Layers3,
  LayoutDashboard, LifeBuoy, LineChart, ListChecks, Menu, Network,
  PackageCheck, PanelLeftClose, PanelLeftOpen, Rocket, Search, Settings,
  ShieldAlert, Sparkles, Target, Timer, TrendingDown, TrendingUp, Users,
  X, Zap
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, LineChart as RLineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart,
  Pie, Cell, Legend
} from "recharts";

import { sendCopilotMessage } from "./services/copilotService";

const NAV = [
  { section: "HOME", icon: Home, items: [["/","Agile Health Dashboard"]] },
  { section: "DELIVERY", icon: KanbanSquare, items: [
    ["/delivery/sprint","Sprint Intelligence"],
    ["/delivery/work-items","Work Item Intelligence"],
    ["/delivery/velocity","Velocity & Trends"],
    ["/delivery/timeline","Events Timeline"],
    ["/delivery/capacity","Capacity & Workload"],
  ]},
  { section: "RISKS", icon: ShieldAlert, items: [
    ["/risks/sprint","Sprint Risk"],
    ["/risks/flow","Flow Intelligence"],
    ["/risks/blockers","Blockers & Dependencies"],
  ]},
  { section: "ENGINEERING", icon: Code2, items: [
    ["/engineering/rework","Rework & Reopened"],
    ["/engineering/quality","Quality & Bugs"],
    ["/engineering/code","Code & PR Intelligence"],
    ["/engineering/builds","Builds & Deployments"],
  ]},
  { section: "RELEASE", icon: Rocket, items: [
    ["/release/intelligence","Release Intelligence"],
  ]},
  { section: "AI COPILOT", icon: Bot, items: [
    ["/copilot/ask","Ask Copilot"],
    ["/copilot/root-cause","Root Cause Analysis"],
    ["/copilot/recommendations","AI Recommendations"],
  ]},
  { section: "ANALYTICS", icon: BarChart3, items: [
    ["/analytics/productivity","Productivity"],
  ]},
];

const sprintData = [
  {name:"S18", planned:42, completed:39},
  {name:"S19", planned:45, completed:41},
  {name:"S20", planned:48, completed:36},
  {name:"S21", planned:50, completed:42},
  {name:"S22", planned:46, completed:38},
  {name:"S23", planned:48, completed:31},
];

const flowData = [
  {name:"Backlog", items:24, avg:2.1, wip:24},
  {name:"Development", items:18, avg:3.6, wip:18},
  {name:"Code Review", items:12, avg:17.2, wip:12},
  {name:"QA", items:19, avg:2.6, wip:19},
  {name:"UAT", items:6, avg:1.6, wip:6},
  {name:"Done", items:32, avg:0.8, wip:0},
];

const commonRows = [
  ["4821","User login improvements","Story","In Progress","Sarah Lee","8/6","High","4d"],
  ["4803","Payment integration","Story","QA","John Doe","13/12","High","3d"],
  ["4812","API optimizations","Story","Blocked","Mike Chen","8/7","Medium","6d"],
  ["4901","UI polish","Task","To Do","Emily Davis","5/0","Low","1d"],
  ["4911","Login fails on mobile","Bug","New","Alex Kim","3/0","High","0d"],
  ["4230","Reporting feature","Feature","In Progress","Priya Shah","20/12","Medium","5d"],
];

function Badge({children, tone="neutral"}) { return <span className={`badge ${tone}`}>{children}</span>; }
function Card({title, children, action}) { return <section className="card"><div className="card-head"><h3>{title}</h3>{action}</div>{children}</section>; }
function Metric({label, value, sub, tone="blue", icon:Icon=Activity}) {
  return <div className="metric"><div className={`metric-icon ${tone}`}><Icon size={18}/></div><div><div className="metric-label">{label}</div><div className="metric-value">{value}</div>{sub && <div className="metric-sub">{sub}</div>}</div></div>;
}
function Progress({value, tone=""}) { return <div className="progress"><span className={tone} style={{width:`${value}%`}}/></div>; }
function RiskRing({value=72, label="High Risk"}) {
  return <div className="risk-ring" style={{"--p": `${value*3.6}deg`}}><div><strong>{value}%</strong><small>{label}</small></div></div>;
}
function MiniSpark({ up = true }) {
  const d = [{ v: 4 }, { v: 7 }, { v: 5 }, { v: 9 }, { v: 8 }, { v: 12 }, { v: 10 }];
  return (
    <div className="mini-spark">
      <ResponsiveContainer width="100%" height={45}>
        <RLineChart data={d}>
          <Line type="monotone" dataKey="v" strokeWidth={2} dot={false} />
        </RLineChart>
      </ResponsiveContainer>
    </div>
  );
}
function Table({headers, rows, riskCol}) {
  return <div className="table-wrap"><table><thead><tr>{headers.map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>
    {rows.map((r,i)=><tr key={i}>{r.map((c,j)=><td key={j}>{riskCol===j ? <Badge tone={String(c).toLowerCase()}>{c}</Badge> : c}</td>)}</tr>)}
  </tbody></table></div>;
}
function PageHeader({eyebrow,title,description,actions}) {
  return <div className="page-header"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div><div className="header-actions">{actions}</div></div>;
}
function ChartTooltip({active,payload,label}) {
  if(!active || !payload?.length) return null;
  return <div className="tooltip"><b>{label}</b>{payload.map((p,i)=><div key={i}>{p.name}: {p.value}</div>)}</div>;
}

function Dashboard({ onSelectionChange }) {
  const organizationId = import.meta.env.VITE_ORGANIZATION_ID;
  const [teams, setTeams] = useState([]);
  const [teamId, setTeamId] = useState("");
  const [sprints, setSprints] = useState([]);
  const [sprintId, setSprintId] = useState("");
  const [sprintMetrics, setSprintMetrics] = useState(null);
  const [deliverySummary, setDeliverySummary] = useState(null);
  const [velocityData, setVelocityData] = useState(null);
  const [loadingTeams, setLoadingTeams] = useState(true);
  const [loadingSprints, setLoadingSprints] = useState(false);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoadingTeams(true);
    setError("");
    setTeams([]);
    setTeamId("");
    if (!organizationId) {
      setError("VITE_ORGANIZATION_ID is missing from frontend/.env.local");
      setLoadingTeams(false);
      return () => { cancelled = true; };
    }
    getDashboardTeams(organizationId)
      .then(data => {
        if (cancelled) return;
        setTeams(data);
        const preferred = data.find(t => t.name === "Synthetic Platform Engineering");
        setTeamId(preferred?.id || data[0]?.id || "");
      })
      .catch(err => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoadingTeams(false); });
    return () => { cancelled = true; };
  }, [organizationId]);

  useEffect(() => {
    let cancelled = false;
    setSprints([]);
    setSprintId("");
    setSprintMetrics(null);
    setDeliverySummary(null);
    setVelocityData(null);
    setError("");
    if (!teamId) return () => { cancelled = true; };
    setLoadingSprints(true);
    getDashboardSprints(organizationId, teamId)
      .then(data => {
        if (cancelled) return;
        setSprints(data);
        const active = data.find(s => s.status === "active");
        setSprintId(active?.id || data[0]?.id || "");
      })
      .catch(err => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoadingSprints(false); });
    return () => { cancelled = true; };
  }, [organizationId, teamId]);

  useEffect(() => {
    onSelectionChange?.({ teamId, sprintId, teamName: teams.find(t => t.id === teamId)?.name || "", sprintName: sprints.find(s => s.id === sprintId)?.name || "" });
  }, [teamId, sprintId, teams, sprints, onSelectionChange]);

  const projectId = sprints.find(s => s.id === sprintId)?.project_id;
  useEffect(() => {
    let cancelled = false;
    setSprintMetrics(null);
    setError("");
    if (!sprintId) { setLoadingMetrics(false); return () => { cancelled = true; }; }
    setLoadingMetrics(true);
    getSprintMetrics(sprintId)
      .then(data => { if (!cancelled) setSprintMetrics(data); })
      .catch(err => { if (!cancelled) setError(`Sprint metrics: ${err.message}`); })
      .finally(() => { if (!cancelled) setLoadingMetrics(false); });
    return () => { cancelled = true; };
  }, [sprintId, refreshKey]);

  useEffect(() => {
    let cancelled = false;
    setDeliverySummary(null);
    if (!organizationId || !teamId || !sprintId) return () => { cancelled = true; };
    getDeliverySummary(organizationId, teamId, sprintId)
      .then(data => { if (!cancelled) setDeliverySummary(data); })
      .catch(err => { if (!cancelled) setError(`Delivery summary: ${err.message}`); });
    return () => { cancelled = true; };
  }, [organizationId, teamId, sprintId, refreshKey]);

  useEffect(() => {
    let cancelled = false;
    setVelocityData(null);
    if (!projectId) return () => { cancelled = true; };
    getProjectVelocity(projectId)
      .then(data => { if (!cancelled) setVelocityData(data); })
      .catch(err => { if (!cancelled) console.warn("Velocity endpoint:", err); });
    return () => { cancelled = true; };
  }, [projectId, refreshKey]);

  // Delivery cards use the live current scope, not the original commitment.
  const fmt = value => value == null ? "—" : Number(value).toLocaleString();
  const pts = value => value == null ? "—" : `${fmt(value)}`;
  const currentScope = deliverySummary?.current_scope;
  const deliveryItems = deliverySummary?.work_items;
  const planned = currentScope?.total_points;
  const completed = currentScope?.completed_points;
  const remaining = currentScope?.remaining_points;
  const completionPercentage = currentScope?.completion_percentage;
  const progress = Math.min(100, Math.max(0, Number(completionPercentage ?? 0)));
  const blocked = deliveryItems?.blocked;
  const reopened = deliveryItems?.reopened;
  const bugs = deliveryItems?.bugs;
  const busy = loadingTeams || loadingSprints || loadingMetrics || (Boolean(sprintId) && !deliverySummary && !error);
  const unavailable = "—";
  const selectedTeam = teams.find(t => t.id === teamId);

  return <>
    <PageHeader
      eyebrow="HOME / AGILE HEALTH"
      title="Agile Health Dashboard"
      description="Good morning Alex! Here’s how your team is doing this sprint."
      actions={<>
        <label className="muted" htmlFor="dashboard-team"></label>
        <select id="dashboard-team" className="btn secondary" value={teamId} disabled={loadingTeams || teams.length === 0}
          onChange={e => setTeamId(e.target.value)} aria-label="Select team">
          {teams.length === 0 && <option value="">No teams</option>}
          {teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <label className="muted" htmlFor="dashboard-sprint"></label>
        <select id="dashboard-sprint" className="btn secondary" value={sprintId} disabled={loadingSprints || sprints.length === 0}
          onChange={e => setSprintId(e.target.value)} aria-label="Select sprint">
          {sprints.length === 0 && <option value="">No sprints</option>}
          {sprints.map(s => <option key={s.id} value={s.id}>{s.name} ({s.status})</option>)}
        </select>
        <button className="btn secondary" disabled={!sprintId || busy} onClick={() => setRefreshKey(n => n + 1)}>Refresh</button>
      </>}
    />
    {busy && <div className="ai-callout" role="status">Loading dashboard data…</div>}
    {error && <div role="alert" className="ai-callout danger-callout"><AlertTriangle size={20}/><div><b>Could not load dashboard</b><p>{error}</p></div></div>}
    {!busy && !error && !teams.length && <div className="ai-callout">No teams found for this organization.</div>}
    {!busy && !error && teams.length > 0 && !sprints.length && <div className="ai-callout">No sprints found for this team.</div>}
    {!busy && !error && sprintMetrics && deliverySummary && <>
      <div className="metric-grid">
        <Metric label="Sprint Health" value={unavailable} sub="Health scoring not yet connected" tone="orange" icon={Gauge}/>
        <Metric label="Delivery Progress" value={`${completionPercentage == null ? "—" : `${Number(completionPercentage).toFixed(2)}%`}`} sub="Current sprint scope completed" tone="blue" icon={Target}/>
        <Metric label="Quality Health" value={unavailable} sub="Health scoring not yet connected" tone="green" icon={CheckCircle2}/>
        <Metric label="Flow Health" value={unavailable} sub="Health scoring not yet connected" tone="orange" icon={Activity}/>
        <Metric label="Engineering Health" value={unavailable} sub="Health scoring not yet connected" tone="blue" icon={Code2}/>
        <Metric label="Team Capacity" value={unavailable} sub="Capacity data not yet connected" tone="purple" icon={Users}/>
        <Metric label="Dependency Risk" value={unavailable} sub="Dependency data not yet connected" tone="orange" icon={Network}/>
        <Metric label="Release Health" value={unavailable} sub="Release data not yet connected" tone="red" icon={Rocket}/>
      </div>
      <div style ={{fontSize:"15px", marginBottom: "20px", marginTop: "20px", fontWeight: 500}}>Sprint Health</div>
      <div className="metric-grid compact">
        <Metric label="Planned" value={pts(planned)} icon={ListChecks}/>
        <Metric label="Completed" value={pts(completed)} icon={CheckCircle2}/>
        <Metric label="Blocked" value={fmt(blocked)} tone="red" icon={ShieldAlert}/>
        <Metric label="Reopened" value={fmt(reopened)} tone="orange" icon={History}/>
        <Metric label="Bugs" value={fmt(bugs)} tone="red" icon={AlertTriangle}/>
        <Metric label="Aging Items" value={fmt(deliveryItems?.aging)} tone="orange" icon={Clock3}/>
        <Metric label="Scope Added" value={deliveryItems?.scope_added_count == null ? "—" : `${fmt(deliveryItems.scope_added_count)}`} tone="red" icon={TrendingUp}/>
      </div>
      <div className="two-col">
        <Card title="Delivery Observations" action={<Badge tone="neutral">Delivery Summary · Live data</Badge>}>
          <div className="ai-callout"><Activity size={20}/><div><b>Selected sprint status</b>
            <p>{fmt(sprintMetrics.completed_work_items)} of {fmt(sprintMetrics.total_work_items)} work items completed; {fmt(sprintMetrics.remaining_work_items)} remaining and {fmt(sprintMetrics.work_in_progress)} in progress.</p>
            <p>{fmt(blocked)} blocked, {fmt(reopened)} reopened and {fmt(bugs)} bugs in the selected sprint. Current scope includes {fmt(deliveryItems?.scope_added_count)} added work items.</p>
          </div></div>
        </Card>
        <Card title={`Sprint Progress — ${sprintMetrics?.sprint_name ?? "Selected Sprint"}`}>
          <div className="big-progress"><span>{fmt(completed)} / {fmt(planned)} points</span><b>{completionPercentage == null ? "—" : `${Number(completionPercentage).toFixed(2)}%`}</b></div>
          <Progress value={progress}/>
          <div className="muted-row"><span>{fmt(remaining)} points remaining</span><span>{sprintMetrics?.sprint_status ?? ""}</span></div>
          <div className="forecast"><div><span>Predicted completion</span><b>Not available</b></div><div><span>Confidence</span><b>Not calculated</b></div></div>
        </Card>
      </div>
       <div className="three-col">
         <Card title="Velocity Trend"><MiniSpark/><b>32 pts</b><span className="positive"> +6% vs prior</span></Card>
         <Card title="Cycle Time"><MiniSpark/><b>4.2 days</b><span className="negative"> +13%</span></Card>
         <Card title="Rework Rate"><MiniSpark/><b>14.2%</b><span className="negative"> +23%</span></Card>
       </div>
    </>}
  </>;
}

function SprintIntelligence({ selectedSprint }) {
  const organizationId = import.meta.env.VITE_ORGANIZATION_ID;
  const [teams, setTeams] = useState([]);
  const [teamId, setTeamId] = useState(selectedSprint?.teamId || "");
  const [sprints, setSprints] = useState([]);
  const [sprintId, setSprintId] = useState(selectedSprint?.sprintId || "");
  const [summary, setSummary] = useState(null);
  const [sprintMetrics, setSprintMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (selectedSprint?.teamId) setTeamId(selectedSprint.teamId);
    if (selectedSprint?.sprintId) setSprintId(selectedSprint.sprintId);
  }, [selectedSprint?.teamId, selectedSprint?.sprintId]);

  useEffect(() => {
    let cancelled = false;
    if (!organizationId) {
      setError("VITE_ORGANIZATION_ID is missing from frontend/.env.local");
      return;
    }
    getDashboardTeams(organizationId)
      .then(data => {
        if (cancelled) return;
        setTeams(data);
        setTeamId(previous => previous || data.find(t => t.name === "Synthetic Platform Engineering")?.id || data[0]?.id || "");
      })
      .catch(err => { if (!cancelled) setError(`Teams: ${err.message}`); });
    return () => { cancelled = true; };
  }, [organizationId]);

  useEffect(() => {
    let cancelled = false;
    setSprints([]);
    setSummary(null);
    setSprintMetrics(null);
    if (!organizationId || !teamId) return () => { cancelled = true; };
    getDashboardSprints(organizationId, teamId)
      .then(data => {
        if (cancelled) return;
        setSprints(data);
        setSprintId(previous => data.some(s => s.id === previous) ? previous : (data.find(s => s.status === "active")?.id || data[0]?.id || ""));
      })
      .catch(err => { if (!cancelled) setError(`Sprints: ${err.message}`); });
    return () => { cancelled = true; };
  }, [organizationId, teamId]);

  useEffect(() => {
    let cancelled = false;
    setSummary(null);
    setSprintMetrics(null);
    if (!organizationId || !teamId || !sprintId) return () => { cancelled = true; };
    setLoading(true);
    setError("");
    Promise.all([
      getDeliverySummary(organizationId, teamId, sprintId),
      getSprintMetrics(sprintId)
    ])
      .then(([delivery, sprint]) => {
        if (!cancelled) { setSummary(delivery); setSprintMetrics(sprint); }
      })
      .catch(err => { if (!cancelled) setError(`Sprint Intelligence: ${err.message}`); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [organizationId, teamId, sprintId, refreshKey]);

  const scope = summary?.current_scope;
  const commitment = summary?.commitment;
  const items = summary?.work_items;
  const fmt = value => value == null ? "—" : Number(value).toLocaleString();
  const pts = value => value == null ? "—" : `${fmt(value)} pts`;
  const percent = value => value == null ? "—" : `${Number(value).toFixed(1)}%`;
  const scopePct = scope?.completion_percentage == null ? 0 : Math.max(0, Math.min(100, Number(scope.completion_percentage)));
  const commitmentPct = commitment?.completion_percentage == null ? 0 : Math.max(0, Math.min(100, Number(commitment.completion_percentage)));
  const daysLeft = (() => {
    if (!sprintMetrics?.end_date) return null;
    const end = new Date(`${String(sprintMetrics.end_date).slice(0, 10)}T00:00:00`);
    if (Number.isNaN(end.getTime())) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return Math.max(0, Math.round((end - today) / 86400000));
  })();
  const selectedTeam = teams.find(t => t.id === teamId);
  const selectedSprintInfo = sprints.find(s => s.id === sprintId);

  return <>
    <PageHeader eyebrow="DELIVERY" title="Sprint Intelligence"
      description="A complete view of the Sprint delivery progress, scope and forecast."
      actions={<>
        <select className="btn secondary" aria-label="Select team" value={teamId}
          onChange={e => { setTeamId(e.target.value); setSprintId(""); }}>
          {!teams.length && <option value="">No teams</option>}
          {teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <select className="btn secondary" aria-label="Select sprint" value={sprintId}
          onChange={e => setSprintId(e.target.value)}>
          {!sprints.length && <option value="">No sprints</option>}
          {sprints.map(s => <option key={s.id} value={s.id}>{s.name} ({s.status})</option>)}
        </select>
        <button className="btn secondary" disabled={!sprintId || loading} onClick={() => setRefreshKey(n => n + 1)}>Refresh</button>
      </>}/>
    {loading && <div className="ai-callout" role="status">Loading Sprint Intelligence data…</div>}
    {error && <div className="ai-callout danger-callout" role="alert"><AlertTriangle size={20}/><div><b>Could not load sprint metrics</b><p>{error}</p></div></div>}
        <div className="metric-grid compact">
          <Metric label="Planned Points" value={(scope?.total_points)} icon={ListChecks}/>
          <Metric label="Completed" value={(scope?.completed_points)} tone="green" icon={CheckCircle2}/>
          <Metric label="Remaining" value={(scope?.remaining_points)} tone="orange" icon={Timer}/>
          <Metric label="Days Left" value={daysLeft == null ? "—" : String(daysLeft)} tone="purple" icon={CalendarClock}/>
          <Metric label="Current Velocity" value={(scope?.completed_points)} icon={TrendingUp}/>
          <Metric label="Avg Velocity" value="—" icon={BarChart3}/>
        </div>
          <div className="metric-grid compact">
          <Metric label="Total Work Items" value={fmt(items?.total)} icon={Layers3}/>
          <Metric label="Completed" value={fmt(sprintMetrics?.completed_work_items)} tone="green" icon={CheckCircle2}/>
          <Metric label="In Progress" value={fmt(items?.in_progress)} icon={Activity}/>
          <Metric label="Blocked" value={fmt(items?.blocked)} tone="red" icon={ShieldAlert}/>
          <Metric label="Scope Added" value={fmt(items?.scope_added_count)} tone="orange" icon={TrendingUp}/>
          <Metric label="Reopened" value={fmt(items?.reopened)} tone="orange" icon={History}/>
        </div>
        <div className="two-col">
          <Card title="Sprint Burndown"><ResponsiveContainer width="100%" height={260}><AreaChart data={sprintData}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis/><Tooltip content={<ChartTooltip/>}/><Area dataKey="planned" name="Planned" fillOpacity={.08}/><Area dataKey="completed" name="Completed" fillOpacity={.18}/></AreaChart></ResponsiveContainer></Card>
          <Card title="Release Burnup"><ResponsiveContainer width="100%" height={260}><AreaChart data={sprintData}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis/><Tooltip content={<ChartTooltip/>}/><Area dataKey="completed" name="Completed" fillOpacity={.18}/><Line dataKey="planned" name="Total Scope" strokeWidth={2}/></AreaChart></ResponsiveContainer></Card>
        </div>
        <Card title="Sprint Forecast"><div className="forecast-grid"><div><span>Predicted completion</span><strong>Sept 21</strong><Badge tone="orange">+1 day</Badge></div><div><span>Expected spillover</span><strong>5–8 pts</strong></div><div><span>Completion probability</span><strong>72%</strong></div><div><span>Confidence interval</span><strong>60–80%</strong></div></div></Card>
  </>;
}

function SprintRisk({ selectedSprint }) {
  const organizationId = import.meta.env.VITE_ORGANIZATION_ID;
  const [teams, setTeams] = useState([]);
  const [teamId, setTeamId] = useState(selectedSprint?.teamId || "");
  const [sprints, setSprints] = useState([]);
  const [sprintId, setSprintId] = useState(selectedSprint?.sprintId || "");
  const [deliverySummary, setDeliverySummary] = useState(null);
  const [sprintMetrics, setSprintMetrics] = useState(null);
  const [velocityData, setVelocityData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (selectedSprint?.teamId) setTeamId(selectedSprint.teamId);
    if (selectedSprint?.sprintId) setSprintId(selectedSprint.sprintId);
  }, [selectedSprint?.teamId, selectedSprint?.sprintId]);

  useEffect(() => {
    let cancelled = false;
    if (!organizationId) { setError("VITE_ORGANIZATION_ID is missing from frontend/.env.local"); return; }
    getDashboardTeams(organizationId)
      .then(data => { if (!cancelled) {
        setTeams(data);
        setTeamId(previous => previous || data.find(t => t.name === "Synthetic Platform Engineering")?.id || data[0]?.id || "");
      }})
      .catch(err => { if (!cancelled) setError(`Teams: ${err.message}`); });
    return () => { cancelled = true; };
  }, [organizationId]);

  useEffect(() => {
    let cancelled = false;
    setSprints([]);
    setDeliverySummary(null);
    setSprintMetrics(null);
    setVelocityData(null);
    if (!organizationId || !teamId) return;
    getDashboardSprints(organizationId, teamId)
      .then(data => { if (!cancelled) {
        setSprints(data);
        setSprintId(previous => data.some(s => s.id === previous) ? previous : (data.find(s => s.status === "active")?.id || data[0]?.id || ""));
      }})
      .catch(err => { if (!cancelled) setError(`Sprints: ${err.message}`); });
    return () => { cancelled = true; };
  }, [organizationId, teamId]);

  const selectedSprintInfo = sprints.find(s => s.id === sprintId);
  const projectId = selectedSprintInfo?.project_id;
  useEffect(() => {
    let cancelled = false;
    setDeliverySummary(null);
    setSprintMetrics(null);
    setVelocityData(null);
    if (!organizationId || !teamId || !sprintId || !projectId) return;
    setLoading(true);
    setError("");
    Promise.all([
      getDeliverySummary(organizationId, teamId, sprintId),
      getSprintMetrics(sprintId),
      getDeliveryVelocity(organizationId, projectId, teamId),
    ])
      .then(([summary, sprint, velocity]) => { if (!cancelled) {
        setDeliverySummary(summary);
        setSprintMetrics(sprint);
        setVelocityData(velocity);
      }})
      .catch(err => { if (!cancelled) setError(`Sprint risk: ${err.message}`); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [organizationId, teamId, sprintId, projectId, refreshKey]);

  const endDate = sprintMetrics?.end_date;
  const daysRemaining = endDate && !Number.isNaN(Date.parse(`${String(endDate).slice(0, 10)}T00:00:00`))
    ? Math.max(0, Math.ceil((new Date(`${String(endDate).slice(0, 10)}T00:00:00`) - new Date()) / 86400000))
    : null;
  const isActive = sprintMetrics?.sprint_status === "active";
  const riskResult = isActive && daysRemaining != null
    ? calculateSprintRisk({ deliverySummary, sprintMetrics, velocityData, daysRemaining })
    : null;
  const riskCategories = [
    ["Sprint Risk", riskResult?.sprintRisk],
    ["Delivery Risk", riskResult?.categories.delivery],
    ["Quality Risk", riskResult?.categories.quality],
    ["Dependency Risk", riskResult?.categories.dependency],
    ["Capacity Risk", riskResult?.categories.capacity],
    ["Scope Risk", riskResult?.categories.scope],
  ];
  const riskTone = value => value == null ? "neutral" : value >= 70 ? "high" : value >= 40 ? "orange" : "green";
  const score = riskResult?.sprintRisk;
  const drivers = riskResult ? [
    [riskResult.indicators.remainingPoints > 0, `${riskResult.indicators.remainingPoints} story points remain in the sprint`, riskTone(riskResult.categories.delivery)],
    [riskResult.indicators.blocked > 0, `${riskResult.indicators.blocked} work items are blocked`, riskTone(riskResult.categories.dependency)],
    [riskResult.indicators.reopened > 0, `${riskResult.indicators.reopened} work items were reopened`, riskTone(riskResult.categories.quality)],
    [riskResult.indicators.scopeGrowth > 0, `Scope grew ${(riskResult.indicators.scopeGrowth * 100).toFixed(1)}% relative to commitment`, riskTone(riskResult.categories.scope)],
  ].filter(row => row[0]) : [];

  return <>
    <PageHeader eyebrow="DELIVERY / RISKS" title="Sprint Risk Assessment"
      description="Sprint completion risk and its contributing factors. Forecasts are not ML-driven"
      actions={<>
        <select className="btn secondary" aria-label="Select team" value={teamId} onChange={e => { setTeamId(e.target.value); setSprintId(""); }}>
          {!teams.length && <option value="">No teams</option>}
          {teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <select className="btn secondary" aria-label="Select sprint" value={sprintId} onChange={e => setSprintId(e.target.value)}>
          {!sprints.length && <option value="">No sprints</option>}
          {sprints.map(s => <option key={s.id} value={s.id}>{s.name} ({s.status})</option>)}
        </select>
        <button className="btn primary" disabled={!projectId || loading} onClick={() => setRefreshKey(n => n + 1)}><Sparkles size={15}/> {loading ? "Calculating…" : "Assess risk"}</button>
      </>}/>
    {error && <div className="ai-callout danger-callout" role="alert"><AlertTriangle size={20}/><p>{error}</p></div>}
    {!error && sprintMetrics && !isActive && <div className="ai-callout">This sprint is {sprintMetrics.sprint_status}. Forward-looking risk scores are shown only for active sprints.</div>}
    {!error && isActive && !riskResult && !loading && <div className="ai-callout">Risk assessment unavailable: complete historical velocity and current delivery data are required.</div>}
    <div className="risk-layout">
      <Card title="Sprint Risk Score"><div className="ring-center">{score == null ? <strong>—</strong> : <RiskRing value={score} label={score >= 70 ? "High Risk" : score >= 40 ? "Medium Risk" : "Low Risk"}/>}</div><p className="center muted">Heuristic risk score, not a probability of missing the sprint goal.</p></Card>
      <Card title="Risk by Category"><div className="risk-bars">{riskCategories.map(([name, value]) => <div key={name}><div><span>{name}</span><b>{value == null ? "—" : `${Math.round(value)}%`}</b></div><Progress value={value ?? 0} tone={riskTone(value)}/></div>)}</div></Card>
    </div>
    <div className="two-col">
      <Card title="Top Risk Drivers">{drivers.length ? drivers.map(([, description, tone], index) => <div className="driver" key={description}><b>{String(index + 1).padStart(2, "0")}</b><span>{description}</span><Badge tone={tone}>{tone === "high" ? "High" : tone === "orange" ? "Medium" : "Low"}</Badge></div>) : <p className="muted">No calculated risk drivers available for this selection.</p>}</Card>
      <Card title="Risk Inputs"><div className="feature-grid">{[
        ["Average velocity", riskResult?.indicators.averageVelocity == null ? "—" : `${riskResult.indicators.averageVelocity} pts`],
        ["Remaining work", riskResult?.indicators.remainingPoints ?? "—"],
        ["Blocked items", riskResult?.indicators.blocked ?? "—"],
        ["Reopened items", riskResult?.indicators.reopened ?? "—"],
        ["Scope growth", riskResult?.indicators.scopeGrowth == null ? "—" : `${(riskResult.indicators.scopeGrowth * 100).toFixed(1)}%`],
        ["Days remaining", riskResult?.indicators.daysRemaining ?? "—"],
      ].map(([name, value]) => <div key={name}><span>{name}</span><b>{value}</b></div>)}</div></Card>
    </div>
  </>;
}

function WorkItems() {
  return <><PageHeader eyebrow="DELIVERY" title="Work Item Intelligence" description="Explore Epics, Features, Stories, Tasks and Bugs with AI risk signals." actions={<button className="btn primary">+ Add filter</button>}/>
    <div className="filterbar"><div className="searchbox"><Search size={16}/><input placeholder="Search work items..."/></div><button className="btn secondary">State: All <ChevronDown size={14}/></button><button className="btn secondary">Risk: All <ChevronDown size={14}/></button></div>
    <Card title="Work Items"><Table headers={["ID","Title","Type","State","Assignee","Est./Act.","Risk","Age"]} rows={commonRows} riskCol={6}/></Card>
  </>;
}

function Velocity({ selectedSprint }) {
  const organizationId = import.meta.env.VITE_ORGANIZATION_ID;
  const [teams, setTeams] = useState([]);
  const [teamId, setTeamId] = useState(selectedSprint?.teamId || "");
  const [sprints, setSprints] = useState([]);
  const [sprintId, setSprintId] = useState(selectedSprint?.sprintId || "");
  const [velocity, setVelocity] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [windowSize, setWindowSize] = useState("6");

  useEffect(() => {
    if (selectedSprint?.teamId) setTeamId(selectedSprint.teamId);
    if (selectedSprint?.sprintId) setSprintId(selectedSprint.sprintId);
  }, [selectedSprint?.teamId, selectedSprint?.sprintId]);

  useEffect(() => {
    let cancelled = false;
    if (!organizationId) {
      setError("VITE_ORGANIZATION_ID is missing from frontend/.env.local");
      return;
    }
    getDashboardTeams(organizationId)
      .then(data => {
        if (cancelled) return;
        setTeams(data);
        setTeamId(previous => previous || data.find(t => t.name === "Synthetic Platform Engineering")?.id || data[0]?.id || "");
      })
      .catch(err => { if (!cancelled) setError(`Teams: ${err.message}`); });
    return () => { cancelled = true; };
  }, [organizationId]);

  useEffect(() => {
    let cancelled = false;
    setSprints([]);
    setVelocity(null);
    if (!organizationId || !teamId) return () => { cancelled = true; };
    getDashboardSprints(organizationId, teamId)
      .then(data => {
        if (cancelled) return;
        setSprints(data);
        setSprintId(previous => data.some(s => s.id === previous) ? previous : (data.find(s => s.status === "active")?.id || data[data.length - 1]?.id || ""));
      })
      .catch(err => { if (!cancelled) setError(`Sprints: ${err.message}`); });
    return () => { cancelled = true; };
  }, [organizationId, teamId]);

  const selectedSprintInfo = sprints.find(s => s.id === sprintId);
  const projectId = selectedSprintInfo?.project_id;
  useEffect(() => {
    let cancelled = false;
    setVelocity(null);
    if (!organizationId || !teamId || !projectId) return () => { cancelled = true; };
    setLoading(true);
    setError("");
    getDeliveryVelocity(organizationId, projectId, teamId)
      .then(data => { if (!cancelled) setVelocity(data); })
      .catch(err => { if (!cancelled) setError(`Historical velocity: ${err.message}`); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [organizationId, teamId, projectId, refreshKey]);

  const history = useMemo(() => [...(velocity?.sprints || [])].sort((a, b) =>
    String(a.end_date || "").localeCompare(String(b.end_date || ""))
  ), [velocity]);
  const selectedIndex = history.findIndex(s => s.sprint_id === sprintId);
  const selected = selectedIndex >= 0 ? history[selectedIndex] : null;
  const endIndex = selectedIndex >= 0 ? selectedIndex + 1 : history.length;
  const windowHistory = history.slice(0, endIndex).slice(windowSize === "all" ? 0 : -Number(windowSize));
  const historyComplete = velocity?.data_complete === true;
  const validHistory = windowHistory.filter(s =>
    Number.isFinite(Number(s.committed_points)) && Number.isFinite(Number(s.completed_points)) &&
    Number(s.unknown_item_count ?? 0) === 0 && Number(s.unknown_points ?? 0) === 0
  );
  const usable = historyComplete && validHistory.length === windowHistory.length && windowHistory.length > 0;
  const mean = (rows, key) => rows.length ? rows.reduce((sum, r) => sum + Number(r[key] || 0), 0) / rows.length : null;
  const spillover = s => Math.max(0, Number(s.committed_points) - Number(s.completed_points));
  const avgSpillover = usable ? validHistory.reduce((sum, s) => sum + spillover(s), 0) / validHistory.length : null;
  const avgVelocityWindow = usable ? mean(validHistory, "velocity") : null;
  const avgPredictabilityWindow = usable ? mean(validHistory, "predictability") : null;
  const fmt = (n, digits = 0) => n == null || !Number.isFinite(Number(n)) ? "—" : Number(n).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
  const pts = n => n == null ? "—" : `${fmt(n, 1)} `;
  const pct = n => n == null ? "—" : `${fmt(n, 1)}%`;
  const chartData = windowHistory.map(s => ({
    name: s.sprint_name, committed: Number(s.committed_points), completed: Number(s.completed_points),
    velocity: Number(s.velocity), predictability: Number(s.predictability),
    spillover: spillover(s)
  }));
  const tableRows = windowHistory.slice().reverse().map(s => [
    s.sprint_name, fmt(s.committed_points, 1), fmt(s.completed_points, 1),
    pts(s.velocity), pct(s.predictability), pts(spillover(s))
  ]);
  const selectedSpillover = selected && Number(selected.unknown_item_count ?? 0) === 0 ? spillover(selected) : null;

  return <>
    <PageHeader eyebrow="DELIVERY / ANALYTICS" title="Velocity & Trends"
      description="Historical delivery patterns across the last six sprints."
      actions={<>
        <select className="btn secondary" aria-label="Select team" value={teamId}
          onChange={e => { setTeamId(e.target.value); setSprintId(""); }}>
          {!teams.length && <option value="">No teams</option>}
          {teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <select className="btn secondary" aria-label="Select sprint" value={sprintId}
          onChange={e => setSprintId(e.target.value)}>
          {!sprints.length && <option value="">No sprints</option>}
          {sprints.map(s => <option key={s.id} value={s.id}>{s.name} ({s.status})</option>)}
        </select>
        <button className="btn secondary" disabled={!projectId || loading} onClick={() => setRefreshKey(n => n + 1)}>Refresh</button>
      </>}/>
    {error && <div className="ai-callout danger-callout" role="alert"><AlertTriangle size={20}/><div><b>Could not load velocity data</b><p>{error}</p></div></div>}
    <div className="metric-grid compact">
      <Metric label="Avg Velocity" value={historyComplete ? pts(velocity?.average_velocity) : "—"} tone="blue" icon={BarChart3}/>
      <Metric label="Selected Sprint Velocity" value={selected ? pts(selected.velocity) : "—"} tone="orange" icon={TrendingUp}/>
      <Metric label="Avg Predictability" value={historyComplete ? pct(velocity?.average_predictability) : "—"}  tone="green" icon={CheckCircle2}/>
      <Metric label="Avg Spillover" value={pts(avgSpillover)}  tone="red" icon={TrendingDown}/>
      <Metric label="Selected Sprint Spillover" value={pts(selectedSpillover)} tone="red" icon={Timer}/>
      <Metric label="Window Avg Velocity" value={pts(avgVelocityWindow)} icon={BarChart3}/>
      <Metric label="Window Avg Predictability" value={pct(avgPredictabilityWindow)} tone="green" icon={Target}/>
    </div>
    <Card title="Committed vs Completed Story Points" action={<select className="btn secondary" aria-label="Historical window" value={windowSize} onChange={e => setWindowSize(e.target.value)}><option value="6">Last 6 sprints</option><option value="10">Last 10 sprints</option><option value="all">All sprints</option></select>}>
      {chartData.length ? <ResponsiveContainer width="100%" height={330}><BarChart data={chartData}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="name" interval={0} angle={-25} textAnchor="end" height={78}/><YAxis/><Tooltip content={<ChartTooltip/>}/><Legend/><Bar dataKey="committed" name="Committed" fill="#64748b"/><Bar dataKey="completed" name="Completed" fill="#2563eb"/></BarChart></ResponsiveContainer> : <p className="muted">No historical sprint data is available for this selection.</p>}
    </Card>
    <div className="two-col">
      <Card title="Historical Velocity Trend">
        {chartData.length ? <ResponsiveContainer width="100%" height={270}><RLineChart data={chartData}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="name" interval="preserveStartEnd"/><YAxis/><Tooltip content={<ChartTooltip/>}/><Line type="monotone" dataKey="velocity" name="Velocity (pts)" stroke="#2563eb" strokeWidth={2} dot/></RLineChart></ResponsiveContainer> : <p className="muted">No velocity trend available.</p>}
      </Card>
      <Card title="Sprint Predictability Trend">
        {chartData.length ? <ResponsiveContainer width="100%" height={270}><RLineChart data={chartData}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="name" interval="preserveStartEnd"/><YAxis domain={[0,100]} tickFormatter={v => `${v}%`}/><Tooltip content={<ChartTooltip/>}/><Line type="monotone" dataKey="predictability" name="Predictability (%)" stroke="#16a34a" strokeWidth={2} dot/></RLineChart></ResponsiveContainer> : <p className="muted">No predictability trend available.</p>}
      </Card>
    </div>
    <div className="metric-grid compact">

    </div>
    <Card title="Sprint History">
      {tableRows.length ? <Table headers={["Sprint", "Committed", "Completed", "Velocity", "Predictability", "Spillover"]} rows={tableRows}/> : <p className="muted">No sprint history returned by the API.</p>}
    </Card>
  </>;
}

function Timeline() {
  const events=[["Sept 10","Sprint started","Sprint 24 began with 48 planned points.","blue"],["Sept 11","Scope changed","Story 4812 added after sprint start.","orange"],["Sept 12","Blocker detected","Story 4820 blocked by API dependency.","red"],["Sept 13","PR rejected","PR #883 required additional changes.","orange"],["Sept 14","Bug created","High-priority mobile login defect opened.","red"],["Sept 15","Story reopened","Story 4801 reopened after QA failure.","red"],["Sept 16","Risk increased","AI sprint risk moved from 61% to 72%.","red"],["Sept 17","AI assessment","Top action: resolve Team B dependency.","blue"]];
  return <><PageHeader eyebrow="DELIVERY" title="Events Timeline" description="A chronological narrative of changes that affected the sprint."/>
    <Card title="Sprint 24 Timeline"><div className="timeline">{events.map((e,i)=><div className="timeline-item" key={i}><div className={`timeline-dot ${e[3]}`}/><div className="timeline-date">{e[0]}</div><div className="timeline-body"><b>{e[1]}</b><p>{e[2]}</p></div></div>)}</div></Card></>;
}

function Capacity() {
  const roles=[["Developers",64],["QA",58],["DevOps",36],["Product",22]];
  return <><PageHeader eyebrow="DELIVERY" title="Capacity & Workload" description="Team capacity, demand and work distribution for the current sprint."/>
    <div className="metric-grid compact"><Metric label="Available" value="320h"/><Metric label="Planned" value="295h"/><Metric label="Remaining" value="142h" tone="orange"/><Metric label="Capacity Used" value="56%" tone="green"/></div>
    <div className="two-col"><Card title="Workload by Role"><div className="role-bars">{roles.map(([r,v])=><div key={r}><div><span>{r}</span><b>{v}%</b></div><Progress value={v}/></div>)}</div></Card>
    <Card title="Capacity vs Demand"><ResponsiveContainer width="100%" height={250}><AreaChart data={[{x:"S19",capacity:320,demand:280},{x:"S20",capacity:315,demand:295},{x:"S21",capacity:310,demand:330},{x:"S22",capacity:325,demand:315},{x:"S23",capacity:320,demand:350},{x:"S24",capacity:320,demand:360}]}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="x"/><YAxis/><Tooltip/><Area dataKey="capacity" fillOpacity={.12}/><Area dataKey="demand" fillOpacity={.08}/></AreaChart></ResponsiveContainer></Card></div>
    <div className="ai-callout"><Sparkles size={20}/><div><b>AI observation</b><p>QA capacity is becoming a constraint relative to the amount of development work expected to enter testing.</p></div></div>
  </>;
}

function Flow() {
  return <><PageHeader eyebrow="RISKS" title="Flow Intelligence" description="Detect bottlenecks, WIP accumulation and abnormal time spent in workflow states."/>
    <div className="flow-strip">{flowData.map((x,i)=><React.Fragment key={x.name}><div className={`flow-stage ${x.name==="Code Review"?"danger":""}`}><b>{x.name}</b><span>{x.items} items</span><small>{x.avg}d avg</small></div>{i<flowData.length-1&&<ChevronRight className="flow-arrow"/>}</React.Fragment>)}</div>
    <Card title="Stage Metrics"><Table headers={["Stage","Items","Avg Time","Median","WIP","Aging"]} rows={flowData.map((x,i)=>[x.name,x.items,`${x.avg}d`,`${Math.max(.6,x.avg*.68).toFixed(1)}d`,x.wip,[5,5,5,2,2,0][i]])}/></Card>
    <div className="ai-callout danger-callout"><AlertTriangle size={20}/><div><b>Code Review bottleneck detected</b><p>Average review time increased from 8h to 17h (+113%). Possible factors: higher PR volume, fewer reviewers, larger PRs and increased rejection rate.</p></div></div>
  </>;
}

function Blockers() {
  const rows=[["4832","API dependency","3 days","Team B","High","High"],["4871","QA environment","2 days","QA Team","Medium","Medium"],["4802","Architecture decision","1 day","Architect","Medium","Medium"],["4900","Third-party service","1 day","Vendor","Low","Low"],["4941","Data migration","6 hours","DB Team","Low","Low"]];
  return <><PageHeader eyebrow="RISKS" title="Blockers & Dependencies" description="Track active blockers and visualize dependencies across teams."/>
    <Card title="Active Blockers"><Table headers={["ID","Title","Blocked Since","Owner","Severity","Impact"]} rows={rows} riskCol={4}/></Card>
    <Card title="Dependency Map"><div className="dependency-map"><div>Team A<br/><b>Story 4812</b></div><ChevronRight/><div>API Team<br/><b>Feature 221</b></div><ChevronRight/><div>Infrastructure<br/><b>Environment</b></div><ChevronRight/><div>QA<br/><b>Testing</b></div></div><div className="ai-callout"><Sparkles size={20}/><div><b>Likely to impact sprint</b><p>Story 4812 has been waiting 2.4 days. Similar dependencies historically take 3–5 days to resolve.</p></div></div></Card>
  </>;
}

function Recommendations({ai=false}) {
  const rows=[["Resolve dependency (4832)","Blocking 3 items","High","Open"],["Prioritize PR review","Review queue growing","High","Open"],["Review sprint scope","Scope +18%","Medium","Open"],["Prioritize QA","QA queue increasing","Medium","Open"],["Review capacity","Demand above capacity","Medium","Open"]];
  return <><PageHeader eyebrow={ai?"AI COPILOT":"RISKS"} title={ai?"AI Recommendations":"Recommendations"} description={ai?"AI-generated actions grounded in current Agile signals.":"Recommended interventions ranked by urgency and supporting evidence."} actions={<button className="btn primary"><Sparkles size={15}/> Refresh</button>}/>
    <Card title="Recommended Actions"><Table headers={["Action","Reason","Impact","Status"]} rows={rows} riskCol={2}/><div className="recommend-actions"><button className="btn primary">Accept selected</button><button className="btn secondary">Assign</button><button className="btn secondary">Dismiss</button><button className="btn secondary">Snooze</button></div></Card>
    <div className="ai-callout"><Sparkles size={20}/><div><b>Feedback improves recommendations</b><p>Record whether a recommendation was accepted, rejected or completed so future recommendation models can learn from outcomes.</p></div></div>
  </>;
}

function Rework({ selectedSprint }) {
  const organizationId = import.meta.env.VITE_ORGANIZATION_ID;
  const [teams, setTeams] = useState([]);
  const [teamId, setTeamId] = useState(selectedSprint?.teamId || "");
  const [sprints, setSprints] = useState([]);
  const [sprintId, setSprintId] = useState(selectedSprint?.sprintId || "");
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  // Keep the dashboard's selection when navigating to Rework & Reopened.
  useEffect(() => {
    if (selectedSprint?.teamId) setTeamId(selectedSprint.teamId);
    if (selectedSprint?.sprintId) setSprintId(selectedSprint.sprintId);
  }, [selectedSprint?.teamId, selectedSprint?.sprintId]);

  useEffect(() => {
    let cancelled = false;
    if (!organizationId) {
      setError("VITE_ORGANIZATION_ID is missing from frontend/.env.local");
      return;
    }
    getDashboardTeams(organizationId)
      .then(data => {
        if (cancelled) return;
        setTeams(data);
        setTeamId(previous => previous || data.find(t => t.name === "Synthetic Platform Engineering")?.id || data[0]?.id || "");
      })
      .catch(err => { if (!cancelled) setError(`Teams: ${err.message}`); });
    return () => { cancelled = true; };
  }, [organizationId]);

  useEffect(() => {
    let cancelled = false;
    setSprints([]);
    setSummary(null);
    if (!organizationId || !teamId) return;
    getDashboardSprints(organizationId, teamId)
      .then(data => {
        if (cancelled) return;
        setSprints(data);
        setSprintId(previous => data.some(s => s.id === previous) ? previous : (data.find(s => s.status === "active")?.id || data[0]?.id || ""));
      })
      .catch(err => { if (!cancelled) setError(`Sprints: ${err.message}`); });
    return () => { cancelled = true; };
  }, [organizationId, teamId]);

  useEffect(() => {
    let cancelled = false;
    setSummary(null);
    if (!organizationId || !teamId || !sprintId) return;
    setLoading(true);
    setError("");
    getDeliverySummary(organizationId, teamId, sprintId)
      .then(data => { if (!cancelled) setSummary(data); })
      .catch(err => { if (!cancelled) setError(`Delivery summary: ${err.message}`); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [organizationId, teamId, sprintId, refreshKey]);

  const total = summary?.work_items?.total;
  const reopened = summary?.work_items?.reopened;
  const rate = total == null || reopened == null || total <= 0
    ? null : (reopened / total) * 100;
  const rateText = rate == null ? "—" : `${rate.toFixed(1)}%`;
  const countText = reopened == null ? "—" : Number(reopened).toLocaleString();

  return <>
    <PageHeader eyebrow="ENGINEERING" title="Rework & Reopened"
      description="Identify hidden delivery effort caused by reopened work, defects and rework."
      actions={<>
        <select className="btn secondary" aria-label="Select team" value={teamId}
          onChange={e => { setTeamId(e.target.value); setSprintId(""); }}>
          {!teams.length && <option value="">No teams</option>}
          {teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <select className="btn secondary" aria-label="Select sprint" value={sprintId}
          onChange={e => setSprintId(e.target.value)}>
          {!sprints.length && <option value="">No sprints</option>}
          {sprints.map(s => <option key={s.id} value={s.id}>{s.name} ({s.status})</option>)}
        </select>
        <button className="btn secondary" disabled={!sprintId || loading} onClick={() => setRefreshKey(n => n + 1)}>Refresh</button>
      </>}/>
    {loading && <div className="ai-callout" role="status">Loading rework metrics…</div>}
    {error && <div className="ai-callout danger-callout" role="alert"><AlertTriangle size={20}/><div><b>Could not load rework metrics</b><p>{error}</p></div></div>}
    <div className="metric-grid compact">
      <Metric label="Rework Rate" value={rateText} tone="orange"/>
      <Metric label="Reopened Items" value={countText} tone="red"/>
      <Metric label="Rework Hours" value="—"/>
      <Metric label="Rework Cost" value="—"/>
    </div>
    <Card title="Reopened Items"><Table headers={["ID","Type","Reason","Reopened On","Additional Effort"]} rows={[["4801","Story","Requirement change","Sep 15","+5h"],["4820","Bug","Failed tests","Sep 14","+4h"],["4855","Story","Incomplete AC","Sep 13","+6h"],["4900","Task","Code review rejection","Sep 12","+2h"],["4902","Bug","Defect found in QA","Sep 11","+3h"]]}/></Card>
    <div className="ai-callout"><Sparkles size={20}/><div><b>Rework increased 3% compared with the previous 4 sprints.</b><p>Top contributing patterns: requirement changes, incomplete acceptance criteria, failed tests and code review rejection.</p></div></div>
  </>;
}

function Quality() {
  const pie=[{name:"Functional",value:38},{name:"Performance",value:20},{name:"Security",value:15},{name:"UX",value:15},{name:"Other",value:12}];
  return <><PageHeader eyebrow="ENGINEERING" title="Quality & Bugs" description="Defect trends, test health and quality signals across the delivery lifecycle."/>
    <div className="metric-grid compact"><Metric label="Bugs Opened" value="24" tone="red"/><Metric label="Bugs Closed" value="18" tone="green"/><Metric label="Defect Density" value="4.2 /KLOC" tone="orange"/><Metric label="Test Pass Rate" value="87%" tone="green"/></div>
    <div className="two-col"><Card title="Bugs Trend"><ResponsiveContainer width="100%" height={260}><BarChart data={[{s:"S18",opened:18,closed:15},{s:"S19",opened:14,closed:16},{s:"S20",opened:20,closed:17},{s:"S21",opened:24,closed:18}]}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="s"/><YAxis/><Tooltip/><Bar dataKey="opened" name="Opened"/><Bar dataKey="closed" name="Closed"/></BarChart></ResponsiveContainer></Card>
    <Card title="Defect Categories"><ResponsiveContainer width="100%" height={260}><PieChart><Pie data={pie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={85} label>{pie.map((_,i)=><Cell key={i}/>)}</Pie><Legend/></PieChart></ResponsiveContainer></Card></div>
    <div className="ai-callout"><Sparkles size={20}/><div><b>Quality signal</b><p>63% of recent defects originated from components that also had above-average code churn.</p></div></div>
  </>;
}

function Code() {
  return <><PageHeader eyebrow="ENGINEERING" title="Code & PR Intelligence" description="Connect pull requests, reviews, code churn and build quality to Agile outcomes."/>
    <div className="metric-grid compact"><Metric label="PRs This Sprint" value="37"/><Metric label="Avg Review Time" value="11.4h" tone="orange"/><Metric label="PR Rejection Rate" value="18%" tone="red"/><Metric label="Build Failure Rate" value="7%" tone="red"/><Metric label="Deployment Failure" value="4%" tone="orange"/><Metric label="Code Churn" value="4,820"/></div>
    <div className="two-col"><Card title="PR Review Time Trend"><ResponsiveContainer width="100%" height={250}><RLineChart data={[{s:"S18",h:8},{s:"S19",h:9},{s:"S20",h:9},{s:"S21",h:12},{s:"S22",h:11},{s:"S23",h:17}]}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="s"/><YAxis/><Tooltip/><Line dataKey="h" name="Hours" strokeWidth={3}/></RLineChart></ResponsiveContainer></Card>
    <Card title="Engineering Signals"><div className="signal-list"><div><span>PR size</span><Badge tone="orange">↑ 31%</Badge></div><div><span>Reviewer workload</span><Badge tone="high">High</Badge></div><div><span>Rejection rate</span><Badge tone="red">18%</Badge></div><div><span>Merge frequency</span><Badge tone="green">4.2/day</Badge></div><div><span>Commit frequency</span><Badge tone="neutral">12/day</Badge></div></div></Card></div>
    <div className="ai-callout"><Sparkles size={20}/><div><b>AI detection</b><p>PR review time increased 42% this sprint. Candidate factors include larger PRs, increased cross-team reviews and reviewer workload.</p></div></div>
  </>;
}

function Builds() {
  return <><PageHeader eyebrow="ENGINEERING" title="Builds & Deployments" description="CI/CD reliability and delivery pipeline intelligence."/>
    <div className="metric-grid compact"><Metric label="Builds" value="146"/><Metric label="Success Rate" value="96%" tone="green"/><Metric label="Failed Builds" value="6" tone="red"/><Metric label="Deployments" value="21"/><Metric label="Deployment Success" value="96%" tone="green"/><Metric label="Rollback Rate" value="4%" tone="orange"/></div>
    <Card title="Pipeline Health"><Table headers={["Pipeline","Builds","Success","Avg Duration","Last Failure","Status"]} rows={[["Web CI","48","98%","7m","Sep 15","Healthy"],["API CI","42","93%","11m","Sep 17","Watch"],["Mobile CI","31","94%","14m","Sep 16","Watch"],["Release","25","96%","18m","Sep 14","Healthy"]]}/></Card>
    <div className="ai-callout"><Sparkles size={20}/><div><b>Pipeline observation</b><p>API CI has the highest failure concentration and is correlated with recent integration work on Feature 221.</p></div></div>
  </>;
}

function Release({readiness=false}) {
  return <><PageHeader eyebrow="RELEASE" title={readiness?"Release Readiness":"Release Intelligence"} description={readiness?"Assess whether the upcoming release has the required evidence to proceed.":"Monitor release health, deployment metrics and unresolved delivery risks."} actions={<button className="btn secondary">Release 2026.09 <ChevronDown size={15}/></button>}/>
    <Card title="Release 2026.09"><div className="release-top"><div><span>Readiness</span><strong>{readiness?"78%":"74%"}</strong><Progress value={readiness?78:74}/></div><div className="release-issues"><div><AlertTriangle size={15}/> Open critical bugs <b>2</b></div><div><GitPullRequest size={15}/> Unmerged PRs <b>4</b></div><div><Network size={15}/> Outstanding dependencies <b>2</b></div><div><Code2 size={15}/> Failed builds <b>3</b></div></div></div></Card>
    <div className="ai-callout danger-callout"><AlertTriangle size={20}/><div><b>Release risk</b><p>Risk increased due to 2 unresolved high-severity defects and 4 PRs awaiting review.</p></div></div>
    <div className="metric-grid compact"><Metric label="Deployment Frequency" value="5/day"/><Metric label="Success Rate" value="96%" tone="green"/><Metric label="Lead Time" value="2.6h"/><Metric label="Change Failure Rate" value="4%" tone="green"/></div>
    <Card title="Release Burnup"><ResponsiveContainer width="100%" height={260}><AreaChart data={sprintData}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis/><Tooltip content={<ChartTooltip/>}/><Area dataKey="planned" name="Planned" fillOpacity={.08}/><Area dataKey="completed" name="Completed" fillOpacity={.18}/></AreaChart></ResponsiveContainer></Card>
    
  </>;
}


function Copilot() {
  const organizationId = import.meta.env.VITE_ORGANIZATION_ID;

  const [messages, setMessages] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const send = async (suggestedQuestion) => {
    const question = (
      typeof suggestedQuestion === "string"
        ? suggestedQuestion
        : q
    ).trim();

    if (!question || loading) return;

    if (!organizationId) {
      setError(
        "VITE_ORGANIZATION_ID is missing from frontend/.env.local"
      );
      return;
    }

    const history = messages.map(m => ({
      role: m.role === "ai" ? "assistant" : "user",
      content: m.text
    }));

    setMessages(prev => [
      ...prev,
      { role: "user", text: question }
    ]);

    setQ("");
    setError("");
    setLoading(true);

    try {
      const answer = await sendCopilotMessage({
        message: question,
        history,
        organizationId
      });

      setMessages(prev => [
        ...prev,
        { role: "ai", text: answer }
      ]);

    } catch (err) {
      setError(
        err.message || "Unable to contact AI Copilot."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHeader
        eyebrow="AI COPILOT"
        title="Ask Copilot"
        description="Ask questions about your Agile delivery data in natural language."
        actions={
          <Badge tone="green">AI online</Badge>
        }
      />

      <div className="copilot-layout">
        <Card title="Ask your Scrum Master Copilot">

          <div className="prompt-chips">
            {[
              "Why is this sprint at risk?",
              "Which stories are most likely to spill over?",
              "What should I discuss in today's stand-up?",
              "Which dependencies need escalation?"
            ].map(x => (
              <button
                key={x}
                disabled={loading}
                onClick={() => send(x)}
              >
                {x}
              </button>
            ))}
          </div>

          <div className="chat" aria-live="polite">
            {messages.length === 0 && (
              <div className="ai-callout">
                <Bot size={20} />
                <div>
                  <b>Welcome to Scrum Master AI Copilot</b>
                  <p>
                    Ask me about sprint performance,
                    delivery risks, blockers, or Agile
                    practices. Include a team and sprint
                    name when requesting specific metrics.
                  </p>
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div
                key={i}
                className={`chat-msg ${m.role}`}
              >
                <div className="avatar">
                  {m.role === "ai"
                    ? <Bot size={16} />
                    : <Users size={16} />}
                </div>

                <div style={{ whiteSpace: "pre-wrap" }}>
                  {m.text}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-msg ai" role="status">
                <div className="avatar">
                  <Bot size={16} />
                </div>
                <div>Copilot is thinking...</div>
              </div>
            )}
          </div>

          {error && (
            <div
              className="ai-callout danger-callout"
              role="alert"
            >
              <AlertTriangle size={18} />
              <div>
                <b>Copilot request failed</b>
                <p>{error}</p>
              </div>
            </div>
          )}

          <div className="chat-input">
            <input
              value={q}
              onChange={e => setQ(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter") {
                  send();
                }
              }}
              placeholder="Ask a question about your sprint..."
              disabled={loading}
            />

            <button
              onClick={() => send()}
              disabled={loading || !q.trim()}
              aria-label="Send message"
            >
              <Sparkles size={16} />
            </button>
          </div>

        </Card>

        {/* Existing Context panel - unchanged */}
        <Card title="Copilot Context">
          <div className="context-list">
            <div>
              <Database size={16} />
              Azure DevOps work items
              <Badge tone="green">Connected</Badge>
            </div>
            <div>
              <GitPullRequest size={16} />
              Git / PR data
              <Badge tone="green">Connected</Badge>
            </div>
            <div>
              <Rocket size={16} />
              Builds & deployments
              <Badge tone="green">Connected</Badge>
            </div>
            <div>
              <BrainCircuit size={16} />
              ML risk model
              <Badge tone="green">Ready</Badge>
            </div>
          </div>
        </Card>

      </div>
    </>
  );
}


function RootCause() {
  return <><PageHeader eyebrow="AI COPILOT / ANALYTICS" title="Root Cause Analysis" description="Explore relationships between delivery outcomes and their contributing signals."/>
    <div className="causal-map"><div><b>Scope Change</b><span>+18%</span></div><ChevronRight/><div><b>WIP</b><span>+22%</span></div><ChevronRight/><div><b>Cycle Time</b><span>+13%</span></div><ChevronRight/><div><b>QA Queue</b><span>+35%</span></div><ChevronRight/><div><b>Rework</b><span>+23%</span></div><ChevronRight/><div className="target"><b>Sprint Completion</b><span>72%</span></div></div>
    <div className="two-col"><Card title="Top Factors Associated With Lower Completion"><div className="factor-list">{[["Scope change","0.82"],["Blocked work","0.76"],["QA capacity","0.69"],["Cycle time","0.64"],["Rework","0.58"]].map(x=><div key={x[0]}><span>{x[0]}</span><Progress value={parseFloat(x[1])*100}/><b>{x[1]}</b></div>)}</div></Card>
    <Card title="Evidence"><div className="ai-callout"><Sparkles size={20}/><div><b>Interpretation</b><p>These relationships are statistical associations, not automatic proof of causation. The strongest signal is the combination of scope change and increasing WIP.</p></div></div><button className="btn secondary">View detailed analysis</button></Card></div></>;
}

function Analytics({type}) {
  const cfg={
    history:["Historical Trends","Compare delivery, quality and flow metrics over time."],
    productivity:["Productivity","Measure throughput, cycle time and flow efficiency at team level."],
    impact:["AI Impact","Measure how AI adoption relates to delivery and quality outcomes."],
    roi:["ROI","Connect improvement initiatives with measurable business and delivery outcomes."]
  }[type];
  const data=[{s:"S18",throughput:39,cycle:3.8},{s:"S19",throughput:41,cycle:3.6},{s:"S20",throughput:36,cycle:4.0},{s:"S21",throughput:42,cycle:4.2},{s:"S22",throughput:38,cycle:4.1},{s:"S23",throughput:31,cycle:4.8}];
  return <><PageHeader eyebrow="ANALYTICS" title={cfg[0]} description={cfg[1]} actions={<button className="btn secondary">Last 6 sprints <ChevronDown size={15}/></button>}/>
    <div className="metric-grid compact"><Metric label="Throughput" value="31 pts" tone="orange"/><Metric label="Cycle Time" value="4.8d" tone="orange"/><Metric label="Flow Efficiency" value="62%" tone="green"/><Metric label={type==="roi"?"Measured Value":"AI Adoption"} value={type==="roi"?"$184K":"68%"} tone="purple"/></div>
    <div className="two-col"><Card title="Trend"><ResponsiveContainer width="100%" height={280}><RLineChart data={data}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="s"/><YAxis/><Tooltip/><Line dataKey="throughput" name="Throughput" strokeWidth={3}/><Line dataKey="cycle" name="Cycle Time" strokeWidth={3}/></RLineChart></ResponsiveContainer></Card>
    <Card title="Key Insights"><div className="insight-list"><div><Sparkles size={16}/><span>Throughput has declined while cycle time increased.</span></div><div><Sparkles size={16}/><span>Scope change is elevated versus the historical baseline.</span></div><div><Sparkles size={16}/><span>Quality and rework should be monitored alongside delivery.</span></div><div><Sparkles size={16}/><span>Use controlled comparisons before attributing gains to AI.</span></div></div></Card></div>
    <Card title="Metric Breakdown"><Table headers={["Metric","Current","Baseline","Change","Interpretation"]} rows={[["Throughput","31 pts","38 pts","-18%","Below baseline"],["Cycle time","4.8d","3.7d","+30%","Watch"],["Flow efficiency","62%","68%","-6%","Watch"],["Rework","14.2%","11.5%","+23%","Elevated"],["Scope change","18%","9%","+100%","High"]]}/></Card>
  </>;
}

function App() {
  const [collapsed,setCollapsed]=useState(false);
  const [mobile,setMobile]=useState(false);
  const [selectedSprint,setSelectedSprint]=useState({ teamId:"", sprintId:"" });
  const handleSelectionChange = React.useCallback(selection => {
    setSelectedSprint(previous => previous.teamId === selection.teamId && previous.sprintId === selection.sprintId ? previous : selection);
  }, []);
  const location=useLocation();
  const pageName=useMemo(()=>NAV.flatMap(s=>s.items).find(x=>x[0]===location.pathname)?.[1]||"Agile Health Dashboard",[location.pathname]);

  return <div className={`app ${collapsed?"collapsed":""} ${mobile?"mobile-nav":""}`}>
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Sparkles size={18}/></div><span>Scrum Master AI</span><button className="icon-btn close-mobile" onClick={()=>setMobile(false)}><X size={18}/></button></div>
      <div className="nav-scroll">{NAV.map(sec=><div className="nav-section" key={sec.section}><div className="nav-section-title"><sec.icon size={13}/><span>{sec.section}</span></div>{sec.items.map(([path,label])=><NavLink key={path} to={path} onClick={()=>setMobile(false)} className={({isActive})=>`nav-item ${isActive?"active":""}`}><span>{label}</span></NavLink>)}</div>)}</div>
      <div className="sidebar-bottom"><NavLink to="/settings" className="nav-item"><Settings size={16}/><span>Settings</span></NavLink></div>
    </aside>
    <main className="main">
      <header className="topbar"><button className="icon-btn mobile-menu" onClick={()=>setMobile(true)}><Menu size={20}/></button><button className="icon-btn collapse-btn" onClick={()=>setCollapsed(!collapsed)}>{collapsed?<PanelLeftOpen size={18}/>:<PanelLeftClose size={18}/>}</button><div className="crumb">Scrum Master AI Cockpit <ChevronRight size={14}/> {pageName}</div><div className="top-actions"><button className="icon-btn"><Search size={18}/></button><button className="icon-btn"><LifeBuoy size={18}/></button><button className="icon-btn notification"><CircleDot size={15}/></button><div className="profile"><div className="avatar">AS</div><div><b>Alex Smith</b><small>Scrum Master</small></div><ChevronDown size={14}/></div></div></header>
      <div className="content"><Routes>
        <Route path="/" element={<Dashboard onSelectionChange={handleSelectionChange}/>}/>
        <Route path="/delivery/sprint" element={<SprintIntelligence selectedSprint={selectedSprint}/>}/>
        <Route path="/delivery/work-items" element={<WorkItems/>}/>
        <Route path="/delivery/velocity" element={<Velocity selectedSprint={selectedSprint}/>}/>
        <Route path="/delivery/timeline" element={<Timeline/>}/>
        <Route path="/delivery/capacity" element={<Capacity/>}/>
        <Route path="/risks/sprint" element={<SprintRisk selectedSprint={selectedSprint}/>}/>
        <Route path="/risks/flow" element={<Flow/>}/>
        <Route path="/risks/blockers" element={<Blockers/>}/>
        <Route path="/engineering/rework" element={<Rework selectedSprint={selectedSprint}/>}/>
        <Route path="/engineering/quality" element={<Quality/>}/>
        <Route path="/engineering/code" element={<Code/>}/>
        <Route path="/engineering/builds" element={<Builds/>}/>
        <Route path="/release/intelligence" element={<Release/>}/>
        <Route path="/copilot/ask" element={<Copilot/>}/>
        <Route path="/copilot/root-cause" element={<RootCause/>}/>
        <Route path="/copilot/recommendations" element={<Recommendations ai/>}/>
        <Route path="/analytics/productivity" element={<Analytics type="productivity"/>}/>
        <Route path="*" element={<Dashboard onSelectionChange={handleSelectionChange}/>}/>
      </Routes></div>
    </main>
  </div>
}
export default App;
