import {DifficultyDisplayProvider} from '@/components/DifficultyDisplay.jsx';
import {ProblemCells,ProblemTableHead,Difficulty,Verdict} from '@/components/ProblemTableParts.jsx';
import BrandWordmark from '../components/BrandWordmark.jsx';
import PagePagination from '@/components/PagePagination.jsx';
import {useFittedPageSize} from '@/lib/useFittedPageSize.js';
import SortDirection from '@/components/SortDirection.jsx';
import RandomProblem from '@/components/RandomProblem.jsx';
import AddToTrainingLists from '@/components/AddToTrainingLists.jsx';
import useNavigationKeys from '@/lib/useNavigationKeys.js';
import useUsage from '@/lib/useUsage.js';
import useContestCalendar from '@/lib/useContestCalendar.js';
import PopConfirm from '@/components/PopConfirm.jsx';
import {matchesShortcut} from '@/lib/shortcuts.js';
import PageSearch from '@/components/PageSearch.jsx';
import FolderSelect from '@/components/FolderSelect.jsx';
import Tooltip from '@/components/Tooltip.jsx';
import PracticeStreak from '@/components/PracticeStreak.jsx';
import {DifficultyBoundsProvider} from '@/components/DifficultyRange.jsx';
import ProfileBadge from '@/components/ProfileBadge.jsx';
import BoundedNumber from '@/components/BoundedNumber.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import { request } from '@/api/client';
import AccountSyncStatus from '@/components/AccountSyncStatus.jsx';
import { useSocial, SocialNotifications } from '@/components/Social.jsx';
import TierIcon from '@/components/TierIcon.jsx';
import ProblemFilters from '@/components/ProblemFilters.jsx';
import {prefetchTrainingLikes} from '@/lib/trainingLikeCache.js';
import {
  useState,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useCallback,
  useDeferredValue,
  memo,
  lazy,
  Suspense,
} from "react";
import {
  BookOpen,
  FlaskConical,
  Library,
  FolderOpen,
  Flag,
  History,
  Network,
  Settings2,
  Settings,
  Search,
  ChevronRight,
  ChevronDown,
  ChevronLeft,
  PanelLeftClose,
  PanelLeftOpen,
  Command,
  Plus,
  X,
  Play,
  Check,
  Star,
  ArrowUp,
  ArrowDown,
  ArrowUpRight,
  LoaderCircle,
  Keyboard,
  Maximize2,
  Minimize2,
  Clock,
  Trophy,
  Medal,
  ListOrdered,
  ListPlus,
  RefreshCw,
  Target,
  Code2,
  Copy,
  BookmarkPlus,
  Layers,
  ArrowLeft,
  Bell,
  Heart,
  ChartNoAxesCombined,
  CalendarDays,
  CalendarClock,
  Activity,
  MinusCircle,
  Award,
  UserRound,
} from "lucide-react";
import InlineTitle from "@/components/InlineTitle.jsx";
import { useSoftwareUpdates, SoftwareUpdatePanel, SoftwareUpdateNotice } from '@/pages/SoftwareUpdates.jsx';
import MockProblemPicker from "./MockProblemPicker.jsx";
import { difficultyBand, difficultyLabel, difficultyDescription, briefSolution } from "@/lib/practiceMetadata.js";
import TitleMedals from '@/components/TitleMedals.jsx';
import { organizeCategories } from "@/models/model.js";
import NavigationSettings, { orderedPages } from "@/pages/NavigationSettings.jsx";
import { AppearanceSettings, TopbarClock } from "@/components/WorkspaceDecorations.jsx";
import GoalsPanel from '@/pages/GoalsPanel.jsx';
import { trainingDay, trainingDateLabel } from "@/lib/trainingDate.js";
import {
  QUEUES,
  verdictLabel,
  verdictTone,
  progressRows,
  shareWorkspace,
  filterRows,
  groupContests,
  categoryCounts,
  remainingSeconds,
  timerText,
  nextSurviving,
  emptyWorkspace,
  isTodayTraining,
  trainingPriority,
  trainingGroup,
} from "@/models/workspaceModel.js";

const loadWorkbench = () => import("./Workbench.jsx");
const Workbench = lazy(loadWorkbench);
const progressPanel = name => lazy(() => import('@/pages/ProgressPanels.jsx').then(module => ({ default: module[name] })));
const GrowthPage = progressPanel('GrowthPage'), ActivityPage = progressPanel('ActivityPage'), CompetitionPage = progressPanel('CompetitionPage');
const UpdatePanel = progressPanel('UpdatePanel'), AchievementPanel = progressPanel('AchievementPanel'), DailyTasks = progressPanel('DailyTasks');
const RankingsPage = lazy(() => import('@/pages/CommunityPanel.jsx'));
const MockSetup = lazy(() => import('@/app/MockSetup.jsx'));
const SubmissionRecords = lazy(() => import('@/pages/SubmissionRecords.jsx'));
const MockHistory = lazy(() => import('@/pages/SubmissionRecords.jsx').then(module => ({ default: module.MockHistory })));
const AvatarSettings = lazy(() => import('@/components/AvatarSettings.jsx'));
const ContestCalendar = lazy(() => import('@/pages/ContestCalendar.jsx'));
const Onboarding = lazy(() => import('@/pages/Onboarding.jsx'));
const LearningPathsPage = lazy(() => import('@/pages/LearningPathsPage.jsx'));
const TemplatesPage=lazy(()=>import('@/pages/TemplatesPage.jsx'));
const TrainingListsPage = lazy(() => import('@/pages/TrainingListsPage.jsx'));
const PreferencesPage = lazy(() => import('@/pages/PreferencesPage.jsx'));

const PAGES = [
  { id: "mine", label: "我的训练", icon: Target, key: "1" },
  { id: "library", label: "题库", icon: Library, key: "2" },
  { id: "training-lists", label: "题单", icon: FolderOpen, key: "" },
  { id: "competitions", label: "比赛", icon: Flag, key: "4" },
  { id: "mock", label: "模拟赛", icon: Clock, key: "5" },
  { id: "records", label: "提交记录", icon: History, key: "6" },
  { id: "growth", label: "成长与能力", icon: ChartNoAxesCombined, key: "7" },
  { id: "activity", label: "活动记录", icon: CalendarDays, key: "8" },
  { id: "lectures", label: "从零讲", icon: BookOpen, key: "9" },
  { id: "templates", label: "模板", icon: Code2, key: "" },
  { id: "paths", label: "算法实验室", icon: FlaskConical, key: "3" },
  { id: "rankings", label: "排行榜", icon: ListOrdered, key: "" },
];
const DEFAULTS = {
  panelStyle: "outlined",
  backdrop: "none",
  widgets: true,
  panelOpacity: 76,
  pageOpacities: {},
  avatarData: '',
  theme: "dark",
  accent: "violet",
  motion: true,
  compact: true,
  libraryPageSize: 50,
  collapsed: false,
  showPlatforms: true,
  onboardingCompleted: false,
  favorites: [],
  views: [],
  readerWidth: 520,
  fontSize: 15,
  difficultyDisplay: 'number',
  learnedLectures: [],
  navOrder: ["mine", "library", "training-lists", "competitions", "mock", "paths", "templates", "rankings", "growth", "records", "activity", "lectures"],
  learningPaths: {},
  shortcuts: {},
  navSchema: 2,
  navLabels: {},
  navGroups: {},
  seenAchievements: [],
  fullscreen: false,
};
function preferencesKey() {
  return window.__tbAccountUserId ? `tb.preferences.v2.${window.__tbAccountUserId}` : 'tb.preferences';
}
function normalizePreferences(saved) {
    const preferences = {
      ...DEFAULTS,
      ...saved,
    };
    preferences.navOrder = (Array.isArray(preferences.navOrder) ? preferences.navOrder : DEFAULTS.navOrder).filter(id => id !== "today");
    if (!saved?.navSchema) preferences.navOrder = [...DEFAULTS.navOrder];
    if (!preferences.navOrder.includes('training-lists')) {
      const libraryIndex = preferences.navOrder.indexOf('library');
      preferences.navOrder.splice(libraryIndex < 0 ? preferences.navOrder.length : libraryIndex + 1, 0, 'training-lists');
    }
    preferences.learnedLectures=Array.isArray(preferences.learnedLectures)?[...new Set(preferences.learnedLectures.filter(value=>typeof value==='string'))]:[];
    preferences.difficultyDisplay=preferences.difficultyDisplay==='text'?'text':'number';
    preferences.motion = true;
    preferences.navSchema = 2;
    preferences.navGroups = { ...preferences.navGroups };
    preferences.navLabels = { ...preferences.navLabels };
    preferences.pageOpacities = { ...preferences.pageOpacities };
    preferences.shortcuts = { ...preferences.shortcuts };
    delete preferences.navGroups.today;
    delete preferences.navLabels.today;
    if (preferences.navGroups.mine?.trim() === "训练与待办") delete preferences.navGroups.mine;
    return preferences;
}
function portablePreferences(preferences) {
  return Object.fromEntries(Object.keys(DEFAULTS).filter(key => key !== 'fullscreen').map(key => [key, preferences[key]]));
}
function readPreferences() {
  try {
    const current = localStorage.getItem(preferencesKey());
    const legacy = !window.__tbAccountUserId || window.__tbOriginalWorkspace ? localStorage.getItem('tb.preferences') : null;
    return normalizePreferences(JSON.parse(current || legacy || '{}'));
  } catch {
    return { ...DEFAULTS };
  }
}
const blankFilters = () => ({
  query: "",
  platform: "",
  shelf: "all",
  category: null,
  min: 800,
  max: 10000,
  kind: "",
  result: "",
  favoritesOnly: false,
  contest: "",
  sort: "contestDate",
  ids: null,
  updateTitle: "",
  desc: false,
  setId: "",
});
const formatDate = (value) =>
  value
    ? new Date(value).toLocaleString("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";
const num = (value) => Number(value || 0).toLocaleString("zh-CN");
const isTyping = (el) =>
  el instanceof Element &&
  !!el.closest('input,textarea,select,[contenteditable="true"],[data-editor]');

function Empty({ icon: Icon = Search, title, description, children }) {
  return (
    <div className="empty">
      <div className="empty-symbol">
        <Icon size={26} />
      </div>
      <h2>{title}</h2>
      <p>{description}</p>
      {children && <div className="empty-actions">{children}</div>}
    </div>
  );
}
function IconButton({ label, icon: Icon, onClick, children, ...props }) {
  return (
    <button
      className="icon-button"
      title={label}
      aria-label={label}
      onClick={onClick}
      {...props}
    >
      {Icon && <Icon size={17} />} {children}
    </button>
  );
}
function Modal({ title, onClose, children, wide = false, footer }) {
  const ref = useRef(null),
    restore = useRef(document.activeElement),
    close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const node = ref.current;
    const focusable = () =>
      [
        ...node.querySelectorAll(
          'button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]',
        ),
      ].filter((el) => el.getClientRects().length);
    (
      focusable().find((el) => el.matches("input")) ||
      focusable()[0] ||
      node
    ).focus();
    const key = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        close.current?.();
      }
      if (e.key === "Tab") {
        const all = focusable();
        if (!all.length) {
          e.preventDefault();
          return;
        }
        const first = all[0],
          last = all.at(-1);
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      if (restore.current?.isConnected) restore.current.focus();
    };
  }, []);
  return (
    <div
      className="modal-overlay"
      onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}
    >
      <section
        className={"modal " + (wide ? "wide" : "")}
        ref={ref}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <header>
          <h2><InlineTitle>{title}</InlineTitle></h2>
          <IconButton label="关闭" icon={X} onClick={onClose} />
        </header>
        <div className="modal-body"><Suspense fallback={<p role="status">正在读取…</p>}>{children}</Suspense></div>
        {footer && <footer>{footer}</footer>}
      </section>
    </div>
  );
}
const SolutionReader=lazy(()=>import('@/components/SolutionReader.jsx'));
const Markdown = lazy(() => import('@/components/SolutionMarkdown.jsx'));
const LecturesPanel = lazy(() => import('@/pages/LecturesPanel.jsx').then(module => ({ default: module.LecturesPanel })));
const LectureDisclosure = lazy(() => import('@/pages/LecturesPanel.jsx').then(module => ({ default: module.LectureDisclosure })));

// Each tree item owns one tab stop. Arrow keys follow the visible tree, rather than the question table.
function KnowledgeTree({
  nodes,
  rows,
  training,
  onFilter,
  selected,
  large = false,
}) {
  const [expanded, setExpanded] = useState(new Set()),
    [focused, setFocused] = useState(null),
    [query, setQuery] = useState("");
  const items = useMemo(() => {
    const out = [];
    const needle = query.trim().toLowerCase();
    const matchesNode = node => !needle || `${node.name} ${(node.tags || []).join(" ")}`.toLowerCase().includes(needle) || (node.children || []).some(matchesNode);
    function walk(branches, parent = null, depth = 0) {
      branches.forEach((node, i) => {
        const key = (parent ? parent + "/" : "") + i + ":" + node.name,
          counts = categoryCounts(node, rows, training);
        if (!counts.available || !matchesNode(node)) return;
        out.push({ node, key, parent, depth, counts });
        if (expanded.has(key) || needle) walk(node.children || [], key, depth + 1);
      });
    }
    walk(nodes);
    return out;
  }, [nodes, rows, training, expanded, query]);
  const expandAll = () => {
    const keys = new Set();
    const walk = (branches, parent = null) => branches.forEach((node, index) => { const key = (parent ? parent + "/" : "") + index + ":" + node.name; if (node.children?.length) keys.add(key); walk(node.children || [], key); });
    walk(nodes); setExpanded(keys);
  };
  const focusKey = items.some((item) => item.key === focused)
    ? focused
    : items[0]?.key;
  const focusItem = (key) => {
    setFocused(key);
    const target = document.querySelector(
      `[data-tree-key="${CSS.escape(key)}"][data-tree-size="${large ? "large" : "small"}"]`,
    );
    if (target) target.focus();
    else
      requestAnimationFrame(() =>
        document
          .querySelector(
            `[data-tree-key="${CSS.escape(key)}"][data-tree-size="${large ? "large" : "small"}"]`,
          )
          ?.focus(),
      );
  };
  const toggle = (key) =>
    setExpanded((current) => {
      const next = new Set(current);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  function keyDown(e, item, index) {
    if (e.ctrlKey || e.altKey || e.metaKey) return;
    if (
      [
        "ArrowDown",
        "ArrowUp",
        "Home",
        "End",
        "ArrowRight",
        "ArrowLeft",
      ].includes(e.key)
    ) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (e.key === "ArrowDown")
      focusItem(items[Math.min(items.length - 1, index + 1)]?.key);
    if (e.key === "ArrowUp") focusItem(items[Math.max(0, index - 1)]?.key);
    if (e.key === "Home") focusItem(items[0]?.key);
    if (e.key === "End") focusItem(items.at(-1)?.key);
    if (e.key === "ArrowRight") {
      if (item.node.children?.length && !expanded.has(item.key))
        toggle(item.key);
      else if (items[index + 1]?.parent === item.key)
        focusItem(items[index + 1].key);
    }
    if (e.key === "ArrowLeft") {
      if (expanded.has(item.key)) toggle(item.key);
      else if (item.parent) focusItem(item.parent);
    }
    if (e.key === "Enter" && !item.node.children?.length) {
      e.preventDefault();
      e.stopPropagation();
      onFilter(item.node);
    }
  }
  return (
    <div className="knowledge-tree-shell">
    {large && <><label className="knowledge-search"><Search size={14} /><input aria-label="搜索完整知识清单" placeholder="搜索知识点" value={query} onChange={event => setQuery(event.target.value)} />{query && <button aria-label="清空知识清单搜索" onClick={() => setQuery("")}><X size={13} /></button>}</label><div className="knowledge-tree-tools"><button onClick={expandAll}>展开全部</button><button onClick={() => { setExpanded(new Set()); setQuery(""); }}>收起全部</button><span>{items.length} 项</span></div></>}
    <div
      className={"knowledge-tree " + (large ? "tree-large" : "")}
      role="tree"
      aria-label={large ? "知识点完整目录" : "知识点目录"}
    >
      {items.map((item, index) => {
        const { node, key, depth, counts } = item,
          kids = !!node.children?.length,
          isOpen = expanded.has(key) || !!query.trim();
        return (
          <div
            className={"tree-line " + (selected === node.name ? "active" : "")}
            key={key}
            data-depth={depth}
            data-branch={kids ? "true" : "false"}
            style={{ "--depth": depth }}
          >
            <button
              role="treeitem"
              aria-level={depth + 1}
              aria-expanded={kids ? isOpen : undefined}
              aria-selected={selected === node.name}
              className="tree-item"
              data-tree-key={key}
              data-tree-size={large ? "large" : "small"}
              tabIndex={focusKey === key ? 0 : -1}
              onFocus={() => setFocused(key)}
              onKeyDown={(e) => keyDown(e, item, index)}
              onClick={() => (kids ? toggle(key) : onFilter(node))}
              title={
                kids
                  ? (isOpen ? "收起" : "展开") + node.name
                  : "筛选 " + node.name
              }
            >
              {kids ? (
                isOpen ? (
                  <ChevronDown size={14} />
                ) : (
                  <ChevronRight size={14} />
                )
              ) : (
                <span className="leaf-dot" />
              )}
              <span className="tree-name">{node.name}</span>
              <span
                className="tree-count"
                aria-label={`题库 ${counts.available} 题，参与 ${counts.active} 题，通过 ${counts.accepted} 题，待办 ${counts.due} 题`}
              >
                <span>{counts.available}</span>
                {!large && counts.active > 0 && (
                  <span className="tree-personal-count">
                    {counts.accepted}/{counts.active}
                    {counts.due > 0 && <em> · {counts.due}待补</em>}
                  </span>
                )}
              </span>
              {large && (
                <>
                  <span className="tree-active">
                    {counts.active ? counts.active + " 题参与" : "—"}
                  </span>
                  <span className="tree-ac">
                    {counts.active
                      ? counts.accepted + "/" + counts.active + " AC"
                      : "尚未开始"}
                  </span>
                </>
              )}
            </button>
            {kids && (
              <button
                className="tree-filter"
                aria-label={"筛选 " + node.name}
                title={"筛选 " + node.name}
                onClick={() => onFilter(node)}
              >
                <ArrowUpRight size={13} />
              </button>
            )}
          </div>
        );
      })}
      {!items.length && <p className="knowledge-empty">没有匹配的知识点</p>}
    </div>
    </div>
  );
}

export default function App() {
  useNavigationKeys();
  const [finishAnchor,setFinishAnchor] = useState(null);
  const [prefs, setPrefs] = useState(readPreferences),
    [data, setData] = useState(null),
    [workspace, setWorkspace] = useState(emptyWorkspace),
    [hub, setHub] = useState(null),
    [insights, setInsights] = useState(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const [page, setPage] = useState("mine"),
    [filters, setFilters] = useState({
      library: blankFilters(),
      mine: blankFilters(),
    });
  const [calendarContest,setCalendarContest]=useState(null);
  const [libraryPage, setLibraryPage] = useState(1);
  const [mockHistoryQuery,setMockHistoryQuery]=useState(""),[mockPreview,setMockPreview]=useState(false);
  const [selected, setSelected] = useState(null),
    [practiceId, setPracticeId] = useState(null),
    [practiceReview, setPracticeReview] = useState(null),
    [mockSlot, setMockSlot] = useState(null),
    [record, setRecord] = useState(null),
    [recordOnlyPending, setRecordOnlyPending] = useState(false),
    [mockTab, setMockTab] = useState("create"),
    [selectedSubmission, setSelectedSubmission] = useState(null),
    [settingsTab, setSettingsTab] = useState(()=>{try{const value=JSON.parse(sessionStorage.getItem(`tb.settings.location.${window.__tbAccount?.userId || window.__tbAccount?.loginId || 'local'}`)||'{}').tab;return ['appearance','interaction','updates','training','help','advanced','accounts','thanks','guide','admin'].includes(value)?value:'home';}catch{return 'home';}});
  const [keyboardSelection, setKeyboardSelection] = useState(false), [listOrder, setListOrder] = useState(null);
  const restoreList = useRef(null);
  const practicePrefetch = useRef(null);
  const labVisit = useRef({leftAt:null,scrollTop:0});
  const templatesVisit=useRef({});
  const trainingListsVisit = useRef({});
  const lecturesVisit = useRef({});
  const [listProblemIds,setListProblemIds]=useState(null);
  const [tourOpen,setTourOpen]=useState(false);
  const [tourContext,setTourContext]=useState('overview');
  const automaticTourStarted=useRef(false);
  const pointerPosition = useRef(null);
  const [hoveredRow, setHoveredRow] = useState(null);
  const [dialog, setDialog] = useState(null),
    [toast, setToast] = useState(null),
    [busy, setBusy] = useState(false),
    [viewName, setViewName] = useState(""),
    [commandQuery, setCommandQuery] = useState("");
  const [readerId, setReaderId] = useState(null),
    [reader, setReader] = useState(null),
    [readerVariant, setReaderVariant] = useState("default"),
    [readerMethod,setReaderMethod]=useState(null),
    [readerError, setReaderError] = useState(""),
    [readerFull, setReaderFull] = useState(false),
    [lectureId, setLectureId] = useState(null),
    [now, setNow] = useState(Date.now());
  const token = useRef(""),
    loadSeq = useRef(0),
    workspaceTime = useRef(0),
    searchRef = useRef(null),
    listRef = useRef(null),
    toastTimer = useRef(null),
    readerSeq = useRef(0),
    contextRef = useRef(null),
    advanceRef = useRef(null),
    visibleRef = useRef([]),
    selectedRef = useRef(null),
    serverOffset = useRef(0),
    previousActive = useRef(null);
  const api = useCallback((path, body) => request(path, body, token.current), []);
  useEffect(()=>{const owner=window.__tbAccountUserId;if(owner)prefetchTrainingLikes(owner,api).catch(()=>{});},[api]);
  const calendar = useContestCalendar(api, Boolean(data), dialog === 'contest-calendar', now);
  const [account, setAccount] = useState(() => window.__tbAccount || null);
  const social = useSocial(api, Boolean(data && account?.userId));
  useUsage(api,data&&account?.userId);
  const [profileSnapshot, setProfileSnapshot] = useState(null), [accountFocus, setAccountFocus] = useState(null);
  useEffect(() => {
    const changed = event => setAccount(previous => shareWorkspace(previous, event.detail));
    window.addEventListener('tb:account-state', changed);
    return () => window.removeEventListener('tb:account-state', changed);
  }, []);
  const profileChanged = useCallback(value => setProfileSnapshot(previous => shareWorkspace(previous, value)), []);
  const preferencesLoaded = useRef(false), uploadedPreferences = useRef(''), preferencesQueue = useRef(Promise.resolve(true));
  const preferencesBaseline = useRef(prefs);
  const [preferencesRevision, setPreferencesRevision] = useState(0);
  useEffect(() => {
    if (!loading && preferencesLoaded.current && !window.__tbAdmin && (window.__tbNewAccount || account?.createdAt) && !prefs.onboardingCompleted && !dialog && !automaticTourStarted.current) {
      automaticTourStarted.current=true;setTourContext('overview');setTourOpen(true);
    }
  }, [loading, preferencesRevision, prefs.onboardingCompleted, dialog,account?.createdAt]);
  function finishOnboarding(overviewCompleted=true) {
    setTourOpen(false);
    if(!overviewCompleted)return;
    window.__tbNewAccount = false;
    try { sessionStorage.removeItem(`tb.onboarding.pending.${(window.__tbAccount?.loginId || '').toLowerCase()}`); } catch { /* Optional device hint. */ }
    setPrefs(previous => ({ ...previous, onboardingCompleted: true }));
    setDialog(null);
  }
  const backgroundRequest = useRef(null), backgroundAgain = useRef(false),
    backgroundSeq = useRef(0), backgroundVersion = useRef(null);
  const refreshBackground = useCallback(function refresh(force = false) {
    if (document.hidden && !force) return Promise.resolve();
    if (backgroundRequest.current) {
      if (force) backgroundAgain.current = true;
      return backgroundRequest.current;
    }
    const seq = ++backgroundSeq.current;
    const pending = Promise.allSettled([
      ["hub?compact=1", setHub], ["insights", setInsights],
    ].map(([path, apply]) => api(path).then(value => {
      if (seq === backgroundSeq.current) apply(previous => shareWorkspace(previous, value));
    }))).finally(() => {
      backgroundRequest.current = null;
      if (backgroundAgain.current) {
        backgroundAgain.current = false;
        return refresh();
      }
    });
    backgroundRequest.current = pending;
    return pending;
  }, [api]);
  const softwareUpdate = useSoftwareUpdates(api, Boolean(data));
  const notice = useCallback((message, type = "info", action = null) => {
    clearTimeout(toastTimer.current);
    setToast({ message, type, action });
    toastTimer.current = setTimeout(() => setToast(null), 4200);
  }, []);
  useEffect(() => {
    if (!window.__tbAccountUserId) return;
    let alive = true, loading = false, timer;
    const load = () => {
      if (!alive || loading || preferencesLoaded.current || document.hidden) return;
      clearTimeout(timer);
      loading = true;
      const pending = preferencesQueue.current.catch(() => false).then(async () => {
        if (!alive) return false;
        try {
          const answer = await api('preferences');
          if (!alive) return false;
          if (answer.preferences) {
            const loaded = normalizePreferences(answer.preferences);
            // Compare uploads with the remote snapshot, not the merged state:
            // changes made while this read was pending still need to be saved.
            uploadedPreferences.current = JSON.stringify(portablePreferences(loaded));
            setPrefs(previous => {
              const merged = { ...loaded, fullscreen: previous.fullscreen };
              for (const key of Object.keys(DEFAULTS)) {
                if (key !== 'seenAchievements' && JSON.stringify(previous[key]) !== JSON.stringify(preferencesBaseline.current[key]))
                  merged[key] = previous[key];
              }
              merged.seenAchievements = [...new Set([
                ...(Array.isArray(loaded.seenAchievements) ? loaded.seenAchievements : []),
                ...(Array.isArray(previous.seenAchievements) ? previous.seenAchievements : []),
              ])];
              return merged;
            });
          }
          preferencesLoaded.current = true;
          setPreferencesRevision(value => value + 1);
          return true;
        } catch (issue) {
          if (alive) {
            notice(`设置读取未完成：${issue.message}`, 'error');
            timer = setTimeout(load, 5000);
          }
          return false;
        } finally { loading = false; }
      });
      preferencesQueue.current = pending;
    };
    const visible = () => { if (!document.hidden) load(); };
    document.addEventListener('visibilitychange', visible);
    window.addEventListener('focus', visible);
    load();
    return () => { alive = false; clearTimeout(timer); document.removeEventListener('visibilitychange', visible); window.removeEventListener('focus', visible); };
  }, [api, notice]);
  useEffect(() => {
    if (!data || !preferencesLoaded.current || !window.__tbAccountUserId) return;
    const value = portablePreferences(prefs), signature = JSON.stringify(value);
    if (signature === uploadedPreferences.current) return;
    const save = () => {
      const pending = preferencesQueue.current.catch(() => false).then(async () => {
        if (signature === uploadedPreferences.current) return true;
        try {
          await api('preferences', { preferences: value });
          uploadedPreferences.current = signature;
          return true;
        } catch (issue) {
          notice(`设置尚未同步：${issue.message}`, 'error');
          return false;
        }
      });
      preferencesQueue.current = pending;
      return pending;
    };
    const timer = setTimeout(save, 600);
    const beforeExit = event => { clearTimeout(timer); event.detail?.waitUntil?.(save()); };
    window.addEventListener('tb-before-update', beforeExit);
    return () => { clearTimeout(timer); window.removeEventListener('tb-before-update', beforeExit); };
  }, [prefs, !!data, preferencesRevision, api, notice]);
  const applyWorkspace = useCallback((value) => {
    if (!value) return;
    const stamp = value.now ? Date.parse(value.now) : Date.now();
    if (stamp >= workspaceTime.current) {
      workspaceTime.current = stamp;
      setWorkspace(previous => shareWorkspace(previous, value));
      if (value.now) {
        serverOffset.current = stamp - Date.now();
        setNow(stamp);
      }
    }
  }, []);
  const reload = useCallback(
    async (initial = false) => {
      const seq = ++loadSeq.current;
      if (initial) setLoading(true);
      try {
        const [library, personal] =
          await Promise.all([
            api("data?compact=1"),
            api("workspace"),
          ]);
        if (seq !== loadSeq.current) return;
        token.current = library.token;
        setData(library);
        applyWorkspace(personal);
        setError("");
        refreshBackground(true);
      } catch (e) {
        if (seq === loadSeq.current) setError(e.message);
      } finally {
        if (seq === loadSeq.current) setLoading(false);
      }
    },
    [api, applyWorkspace, refreshBackground],
  );
  useEffect(() => {
    reload(true);
    return () => {
      loadSeq.current++;
      backgroundSeq.current++;
      backgroundAgain.current = false;
      clearTimeout(toastTimer.current);
    };
  }, [reload]);
  useEffect(() => {
    try { localStorage.setItem(preferencesKey(), JSON.stringify(prefs)); } catch { /* SQLite/cloud still retain account preferences. */ }
    const root = document.documentElement;
    root.dataset.panelStyle = prefs.panelStyle;
    root.dataset.backdrop = prefs.backdrop;
    root.style.setProperty('--panel-opacity', `${Math.min(100, Math.max(0, Number(prefs.panelOpacity ?? 76)))}%`);
    for (const [key, value] of Object.entries(prefs.pageOpacities || {}))
      root.style.setProperty(`--opacity-${key}`, `${Math.min(100, Math.max(0, Number(value) || 0))}%`);
    for (const key of ['mine','library','competitions','mock','paths','templates','rankings','growth','records','activity','lectures','settings','statement','editor','solution'])
      if (prefs.pageOpacities?.[key] == null) root.style.removeProperty(`--opacity-${key}`);
    root.dataset.theme = prefs.theme;
    root.dataset.accent = prefs.accent;
    root.dataset.motion = "on";
    root.dataset.density = prefs.compact ? "compact" : "comfortable";
    root.style.setProperty(
      "--ui-font-size",
      `${Math.min(22, Math.max(13, Number(prefs.fontSize) || 15))}px`,
    );
  }, [prefs]);
  // 桌面全屏：浏览器测试环境没有原生窗口，available=false 时设置项禁用。
  const [display, setDisplay] = useState({ available: false, fullscreen: false });
  const applyFullscreen = useCallback(async (value) => {
    try {
      const answer = await api("desktop/fullscreen", { fullscreen: !!value });
      setDisplay({ available: !!answer.available, fullscreen: !!answer.fullscreen });
    } catch { /* 浏览器里没有原生窗口，忽略。 */ }
  }, [api]);
  useEffect(() => {
    let alive = true;
    api("desktop/fullscreen")
      .then(answer => { if (alive && answer && typeof answer.available === "boolean") setDisplay({ available: !!answer.available, fullscreen: !!answer.fullscreen }); })
      .catch(() => {});
    const onKey = (event) => {
      if (event.key === "F11" && !event.ctrlKey && !event.altKey && !event.metaKey) {
        event.preventDefault();
        setDisplay(previous => { if (previous.available) applyFullscreen(!previous.fullscreen); return previous; });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => { alive = false; window.removeEventListener("keydown", onKey); };
  }, [api, applyFullscreen]);
  useEffect(() => {
    if (!workspace.activeContest) return;
    setNow(Date.now() + serverOffset.current);
    const tick = setInterval(
      () => { if (!document.hidden) setNow(Date.now() + serverOffset.current); },
      1000,
    );
    return () => clearInterval(tick);
  }, [workspace.activeContest?.id]);
  useEffect(() => {
    if (!data) return;
    let active = true, pending = false;
    const refresh = () => {
      if (!active || pending || document.hidden) return;
      pending = true;
      return api("workspace")
        .then(value => { if (active) applyWorkspace(value); })
        .catch(() => {})
        .finally(() => { pending = false; });
    };
    const timer = setInterval(
      refresh,
      workspace.activeContest || workspace.summary?.pending ? 2500 : 15000,
    );
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      active = false;
      clearInterval(timer);
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, [
    !!data,
    workspace.activeContest?.id,
    workspace.summary?.pending,
    api,
    applyWorkspace,
  ]);
  useEffect(() => {
    const old = previousActive.current;
    if (old && !workspace.activeContest) {
      const finished = workspace.contests.find((c) => c.id === old);
      if (finished && page === "mock") {
        setRecord(finished);
        setPage("mock");
        setMockTab("history");
        setRecordOnlyPending(false);
        if (Date.parse(finished.deadline) <= Date.now() + serverOffset.current) notice("计时结束，提交记录已保存，可以开始复盘");
      }
    }
    previousActive.current = workspace.activeContest?.id || null;
  }, [workspace.activeContest?.id, workspace.contests, page, notice]);
  useEffect(() => {
    if (
      workspace.activeContest &&
      remainingSeconds(workspace.activeContest, now) === 0
    )
      api("workspace")
        .then(applyWorkspace)
        .catch(() => {});
  }, [
    workspace.activeContest?.id,
    Math.floor(now / 10000),
    api,
    applyWorkspace,
  ]);
  useEffect(() => {
    if (!data) return;
    const version = [workspace.summary?.attempts, workspace.summary?.total, workspace.summary?.accepted].join(":");
    const changed = backgroundVersion.current !== null && version !== backgroundVersion.current;
    backgroundVersion.current = version;
    refreshBackground(changed);
    const timer = setInterval(() => refreshBackground(), hub?.sync?.busy ? 3000 : 60000);
    const visible = () => { if (!document.hidden) refreshBackground(); };
    document.addEventListener('visibilitychange', visible);
    return () => { clearInterval(timer); document.removeEventListener('visibilitychange', visible); };
  }, [
    !!data,
    workspace.summary?.attempts,
    workspace.summary?.total,
    workspace.summary?.accepted,
    hub?.sync?.busy,
    refreshBackground,
  ]);
  useEffect(() => {
    if (!hub?.sync?.lastSuccessAt) return;
    let cancelled = false;
    Promise.all([api("data?compact=1"), api("workspace")])
      .then(([library, personal]) => {
        if (cancelled) return;
        token.current = library.token;
        setData(library);
        applyWorkspace(personal);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [hub?.sync?.lastSuccessAt, api, applyWorkspace]);
  const rows = useMemo(
      () => progressRows(data?.rows || [], workspace),
      [data?.rows, workspace.training, workspace.activeContest, workspace.contests, workspace.completedReplayContests],
    );
  const mine = useMemo(()=>{
    const result=new Map(rows.filter(row=>row.active).map(row=>[row.id,row])),catalog=new Map(rows.map(row=>[row.id,row]));
    for(const task of workspace.goalTasks||[]){const row=catalog.get(task.id);result.set(task.id,{...task,...row,tags:row?.tags||[],accepted:!!(row?.accepted||task.accepted),goalTask:true,goalTitles:task.goalTitles||[]});}
    return [...result.values()];
  },[rows,workspace.goalTasks]);
  const currentTrainingDay = trainingDay(workspace.now || now);
  const todayMine = useMemo(() => mine.filter(row => row.goalTask || isTodayTraining(row, workspace.now || now)), [mine, currentTrainingDay]);
  const categories = useMemo(
    () => organizeCategories(data?.categories || []),
    [data?.categories],
  );
  const libraryQuery = useDeferredValue(filters.library.query),
    mineQuery = useDeferredValue(filters.mine.query);
  const currentFilters = filters[page] || blankFilters(),
    query = page === "mine" ? mineQuery : libraryQuery;
  const visible = useMemo(() => {
    if (!["library", "mine"].includes(page)) return [];
    const base = page === "mine" ? todayMine : rows.filter(row => !row.catalogHidden),
      params = { ...currentFilters, query, favorites: prefs.favorites };
    let filtered = filterRows(base, params);
    if (page === "mine" && params.setId === "@single") {
      const grouped = new Set([...workspace.sets.flatMap(set => set.ids || []), ...workspace.contests.flatMap(contest => contest.slots?.map(slot => slot.id) || [])]);
      filtered = filtered.filter(row => !grouped.has(row.id));
    } else if (page === "mine" && params.setId) {
      const set =
        workspace.sets?.find((s) => s.id === params.setId) ||
        workspace.contests?.find((s) => s.id === params.setId);
      const ids = new Set(set?.ids || set?.slots?.map((s) => s.id) || []);
      filtered = filtered.filter((r) => ids.has(r.id));
    }
    if (page === "mine") {
      filtered.sort((left, right) => trainingPriority(left) - trainingPriority(right));
    }
    if (listOrder?.page === page && listOrder.filters === currentFilters && listOrder.query === query) {
      const positions = new Map(listOrder.ids.map((id, index) => [id, index]));
      filtered.sort((left, right) => (positions.get(left.id) ?? Infinity) - (positions.get(right.id) ?? Infinity));
    }
    return filtered;
  }, [
    page,
    todayMine,
    rows,
    workspace.goalTasks,
    currentFilters,
    query,
    prefs.favorites,
    workspace.sets,
    workspace.contests,
    listOrder,
  ]);
  const libraryPageSize=useFittedPageSize(listRef,`${page}:${Boolean(data)}:${Boolean(practiceId)}`,"tbody tr[data-id]");
  const libraryPages = Math.max(1, Math.ceil(visible.length / libraryPageSize)),
    currentLibraryPage = Math.min(libraryPage, libraryPages),
    libraryStart = (currentLibraryPage - 1) * libraryPageSize;
  const displayedRows = useMemo(
    () => page === "library" ? visible.slice(libraryStart, libraryStart + libraryPageSize) : visible,
    [page, visible, libraryStart, libraryPageSize],
  );
  useEffect(() => { setLibraryPage(1); }, [filters.library, libraryQuery]);
  useEffect(() => { if (page === "library") setLibraryPage(currentLibraryPage); }, [page, currentLibraryPage]);
  useEffect(() => { if (page === "library") listRef.current?.scrollTo({ top: 0 }); }, [page, currentLibraryPage, libraryPageSize]);
  visibleRef.current = visible;
  selectedRef.current = selected;
  useEffect(() => {
    if (!["mine", "library"].includes(page) || practiceId) return;
    if (selected && !displayedRows.some((r) => r.id === selected)) setSelected(null);
  }, [displayedRows, page, practiceId, selected]);
  useEffect(() => {
    if (practiceId || !selected || !keyboardSelection) return;
    const element = listRef.current?.querySelector(
      `tr[data-id="${CSS.escape(selected)}"]`,
    );
    element?.scrollIntoView({ block: "nearest" });
  }, [selected, keyboardSelection]);
  useLayoutEffect(() => {
    const saved = restoreList.current, list = listRef.current;
    if (practiceId || !saved || !list || saved.page !== page) return;
    list.scrollTop = saved.scrollTop;
    list.scrollLeft = saved.scrollLeft;
    list.focus({ preventScroll: true });
    restoreList.current = null;
  }, [practiceId, page, displayedRows]);
  const active = workspace.activeContest,
    summary = workspace.summary || emptyWorkspace.summary;
  const labFocus=page==='paths'&&Boolean(prefs.learningPaths?.activePath)&&!practiceId;
  const mockFocus = page === "mock" && active && mockTab === "create" && !record && !practiceId;
  const lastWorkspacePage = useRef("mine");
  useEffect(()=>{if(page!=="settings")lastWorkspacePage.current=page;},[page]);
  const passedCount = mine.filter((r) => r.accepted).length,
    totalCount = mine.length,
    dueCount = mine.filter((r) => r.queue).length;
  const setFilter = (patch, target = page) =>
    setFilters((current) => ({
      ...current,
      [target]: { ...current[target], ...patch, ...(target === "mine" ? { platform: "", shelf: "all", setId: "" } : {}) },
    }));
  function go(next) {
    setKeyboardSelection(false);
    setSelected(null);
    setListOrder(null);
    document.querySelectorAll(".topbar details[open]").forEach(node => node.removeAttribute("open"));
    setPracticeId(null);
    setRecord(null);
    setPage(next === "goals" ? "growth" : next);
    if (next === "goals") setTimeout(() => document.getElementById("growth-goals")?.scrollIntoView({ behavior: "smooth" }), 100);
    setReaderId(null);
    setReaderFull(false);
    setDialog(null);
    requestAnimationFrame(() => listRef.current?.focus());
  }
  function filterCategory(node, explicitTarget) {
    const target =
      explicitTarget ||
      (["mine", "library"].includes(page) && mine.length ? page : "library");
    setPracticeId(null);
    setPage(target);
    setFilter({ category: node, setId: "" }, target);
    notice("已筛选：" + node.name);
    requestAnimationFrame(() => listRef.current?.focus());
  }
  async function openUpdate(notification) {
    try {
      const library = await api("data");
      setData(library);
      const targets = new Set([...(notification.problemIds || []), ...(notification.solutionIds || [])]);
      const urls = new Set((notification.problemUrls || []).map(url => String(url).replace(/[?#].*$/, "").replace(/\/$/, "")));
      const ids = library.rows.filter(row => targets.has(row.id) || urls.has(String(row.url || "").replace(/[?#].*$/, "").replace(/\/$/, ""))).map(row => row.id);
      if (!ids.length) {
        notice(notification.url ? "该内容尚未加入本地题库，可查看通知中的仓库链接" : "这条旧通知没有可核对的具体题目，新的通知会保留题目列表");
        return;
      }
      go("library");
      setFilter({ ...blankFilters(), ids, updateTitle: notification.title }, "library");
      setSelected(ids[0]);
      api("hub/dismiss", { id: notification.id }).then(setHub).catch(() => {});
      focusList();
    } catch (e) { notice(e.message, "error"); }
  }
  function resetFilters() {
    setFilters((f) => ({ ...f, [page]: blankFilters() }));
  }
  function toggleFavorite(id) {
    setPrefs((p) => ({
      ...p,
      favorites: p.favorites.includes(id)
        ? p.favorites.filter((x) => x !== id)
        : [...p.favorites, id],
    }));
  }
  function focusList() {
    requestAnimationFrame(() => listRef.current?.focus({ preventScroll: true }));
  }
  async function openPractice(id, { assisted = false, problemIds = null } = {}) {
    if (!id || busy) return;
    if (active?.slots.some((s) => s.id === id)) {
      setReaderId(null);
      setPracticeId(null);
      setPage("mock");
      setMockSlot(id);
      return;
    }
    setBusy(true);
    void loadWorkbench().catch(()=>{});
    // Start the bounded statement fetch while training activation is persisted.
    const prepared = api(`problem?id=${encodeURIComponent(id)}&background=1`).catch(()=>null);
    const list = listRef.current;
    const context = contextRef.current && practiceId ? contextRef.current : {
      page, ids: problemIds || visibleRef.current.map(row => row.id), id, libraryPage: currentLibraryPage,
      scrollTop: list?.scrollTop || 0, scrollLeft: list?.scrollLeft || 0,
    };
    if (list) {
      setListOrder({ page, filters: currentFilters, query, ids: context.ids });
    }
    pointerPosition.current = null;
    setHoveredRow(null);
    setKeyboardSelection(false);
    try {
      const result = await api("training/start", { id, deferWorkspace:true, ...(assisted ? { assisted: true } : {}) });
      if (result.workspace) applyWorkspace(result.workspace);
      else void api('workspace').then(applyWorkspace).catch(()=>{});
      practicePrefetch.current = !result.reviewTask && !result.workspace?.activeContest ? {id,promise:prepared} : null;
      contextRef.current = context;
      advanceRef.current = null;
      setPracticeId(id);
      setPracticeReview(result.reviewTask || null);
      setReaderId(null);
      setReaderFull(false);
    } catch (e) {
      notice(e.message, "error");
    } finally {
      setBusy(false);
    }
  }
  async function removeTraining(id) {
    if (!id || busy) return;
    setBusy(true);
    try {
      const ids = visibleRef.current.map((r) => r.id);
      const result = await api("training/remove", { id });
      applyWorkspace(result.workspace);
      setSelected(
        nextSurviving(
          ids,
          id,
          ids.filter((x) => x !== id),
        ),
      );
      notice("已取消训练，代码与历史记录保留。", "info", {
        label: "恢复",
        run: async () => {
          try {
            const restored = await api("training/start", { id });
            applyWorkspace(restored.workspace);
            setSelected(id);
            notice("已恢复训练");
            focusList();
          } catch (e) {
            notice(e.message, "error");
          }
        },
      });
      focusList();
    } catch (e) {
      notice(e.message, "error");
    } finally {
      setBusy(false);
    }
  }
  function progressChanged(value) {
    const id = practiceId;
    if (id) {
      const previous = workspace.training.find((r) => r.id === id),
        next = value.training.find((r) => r.id === id);
      if (next?.accepted && (!previous?.accepted || (previous.reviewTask && !next.reviewTask))) advanceRef.current = id;
    }
    applyWorkspace(value);
  }
  function exitPractice() {
    const context = contextRef.current;
    setPracticeId(null);
    setReaderId(null);
    if (context) {
      if (page === "library") setLibraryPage(context.libraryPage || 1);
      restoreList.current = context;
    }
    setSelected(null);
    setKeyboardSelection(false);
    advanceRef.current = null;
    focusList();
    api("workspace")
      .then(applyWorkspace)
      .catch(() => {});
  }
  async function nextPractice() {
    const context = contextRef.current;
    const ids = context?.ids || visibleRef.current.map((r) => r.id);
    const index = ids.indexOf(practiceId);
    const next = ids[index + 1];
    if (next) {
      await openPractice(next);
    } else {
      exitPractice();
      notice("这组题已经到最后一题");
    }
  }
  async function startOriginalContest(name) {
    setBusy(true);
    try {
      const result = await api("training/contest", { contest: name });
      applyWorkspace(result.workspace);
      setPage("mine");
      setPracticeId(null);
      setFilter({ ...blankFilters(), setId: result.set.id }, "mine");
      setSelected(result.set.ids[0]);
      notice("已加入训练：" + name);
      focusList();
    } catch (e) {
      notice(e.message, "error");
    } finally {
      setBusy(false);
    }
  }
  const replayStarting = useRef(false);
  async function startReproduction(name) {
    if (replayStarting.current) return;
    if (workspace.activeContest) {
      go('mock');
      notice('请先完成当前比赛');
      return;
    }
    replayStarting.current = true;
    setBusy(true);
    try {
      const { events = [] } = await api('contests/events');
      const event = events.find(item => item.name === name);
      if (!event) throw new Error('这场比赛暂不能开始重现赛，请刷新比赛列表');
      const { plan } = await api('contests/preview', {
        mode: 'replay', contest: name, duration: event.duration, rules: event.rules,
        wrongPenalty: 20, compilePenalty: false,
      });
      const result = await api('contests/start', {
        previewId: plan.previewId, ids: plan.slots.map(slot => slot.id),
        duration: event.duration, name: plan.name,
      });
      startedMock(result);
    } catch (issue) { notice(issue.message, 'error'); }
    finally { replayStarting.current = false; setBusy(false); }
  }
  function openAccounts(section = 'accounts') {
    setAccountFocus(previous => ({ section, request: (previous?.request || 0) + 1 }));
    go('settings');
    setSettingsTab('accounts');
  }
  function startedMock(result) {
    applyWorkspace(result.workspace);
    setPracticeId(null);
    setReaderId(null);
    setReader(null);
    setReaderFull(false);
    setPage("mock");
    setMockTab("create");
    setMockSlot(result.contest.slots[0]?.id);
    notice("计时已开始，祝你专注", "success");
  }
  async function finishMock(cancelled=false) {
    if (!active || busy) return;
    setBusy(true);
    try {
      const {saveBeforeUpdate}=await import('./Workbench.jsx');
      await saveBeforeUpdate('草稿尚未保存，请保存成功后再结束或取消比赛。');
      const result = await api(cancelled?"contests/cancel":"contests/finish", { contestId: active.id });
      applyWorkspace(result.workspace);
      setRecord(cancelled?null:result.contest);
      setPage("mock");
      setMockTab(cancelled?"create":"history");
      setDialog(null);
      setReaderId(null);
      setPracticeId(null);
      setMockFocus(false);
      setFinishAnchor(null);
      notice(cancelled?"比赛已取消":"比赛已结束，可以开始复盘");
    } catch (e) {
      notice(e.message, "error");
    } finally {
      setBusy(false);
    }
  }
  async function openRecord(contest) {
    try {
      const result = await api("contest?id=" + encodeURIComponent(contest.id));
      setRecord(result.contest);
      setPage("mock");
      setMockTab("history");
      setRecordOnlyPending(false);
      setPracticeId(null);
    } catch (e) {
      notice(e.message, "error");
    }
  }
  async function openSolution(id,methodId) {
    if (!id) return;
    if (practiceId !== id) { await openPractice(id); return; }
    if(readerId===id){if(methodId)setReaderMethod(methodId);return;}
    if (active?.slots.some((slot) => slot.id === id)) {
      notice("比赛进行中，结束后可查看题解", "error");
      return;
    }
    const sequence = ++readerSeq.current;
    setReaderId(id);
    setReaderFull(false);
    setReader(null);
    setReaderVariant("default");
    setReaderMethod(methodId||null);
    setReaderError("");
    try {
      const result = await api("solution?id=" + encodeURIComponent(id));
      if (readerSeq.current === sequence) {
        setReader(result);
        api("workspace")
          .then(applyWorkspace)
          .catch(() => {});
      }
    } catch (e) {
      if (readerSeq.current === sequence) setReaderError(e.message);
    }
  }
  useEffect(() => {
    if (readerId && active?.slots.some((slot) => slot.id === readerId)) {
      readerSeq.current++;
      setReaderId(null);
      setReader(null);
      setReaderFull(false);
    }
  }, [active?.id, readerId]);
  const copy = useCallback(async (text) => {
    try {
      await navigator.clipboard.writeText(String(text).replace(/\n$/, ""));
      notice("已复制");
    } catch {
      notice("复制未完成，请选择文字后按 Ctrl+C", "error");
    }
  }, [notice]);
  function resizeReader(e) {
    const start = e.clientX,
      width = prefs.readerWidth;
    const controller = new AbortController();
    e.currentTarget.setPointerCapture?.(e.pointerId);
    window.addEventListener(
      "pointermove",
      (event) =>
        setPrefs((p) => ({
          ...p,
          readerWidth: Math.min(
            900,
            Math.max(340, width + start - event.clientX),
          ),
        })),
      { signal: controller.signal },
    );
    window.addEventListener("pointerup", () => controller.abort(), {
      once: true,
      signal: controller.signal,
    });
  }
  const commands = [
    ...orderedPages(PAGES, prefs).map((p) => ({
      name: "打开" + p.label,
      detail: p.key ? "Ctrl+" + p.key : "",
      action: () => go(p.id),
    })),
    {
      name: "查看训练待办",
      detail: "Ctrl+3",
      action: () => { go("mine"); setFilter(blankFilters(), "mine"); },
    },
    {
      name: "收起 / 展开侧栏",
      detail: "Ctrl+B",
      action: () => setPrefs((p) => ({ ...p, collapsed: !p.collapsed })),
    },
    {
      name: "搜索当前页面",
      detail: "Ctrl+F",
      action: () => searchRef.current?.focus(),
    },
    {
      name: "切换深浅主题",
      action: () =>
        setPrefs((p) => ({
          ...p,
          theme: p.theme === "dark" ? "light" : "dark",
        })),
    },
    { name: "快捷键设置", action: () => {setPage("settings");setSettingsTab("training");} },
    { name: "查看训练概览", action: () => setDialog("summary") },
    { name: "设置", detail: "Ctrl+,", action: () => go("settings") },
  ];
  useEffect(() => {
    function keyboard(e) {
      if (e.defaultPrevented || e.isComposing || e.target.closest?.('[data-shortcut-input]')) return;
      if (e.key==='Escape' && (document.querySelector('.filter-popover') || document.querySelector('.tb-select-menu') || document.querySelector('[data-popconfirm]'))) return;
      if (e.key==='Escape' && e.target.closest?.('.tooltip-anchor') && document.querySelector('[role="tooltip"]')) return;
      const shortcut=id=>matchesShortcut(e,id,prefs.shortcuts);
      if (document.querySelector('dialog[open],[aria-modal="true"]')) return;
      const control = e.ctrlKey || e.metaKey,
        typing = isTyping(e.target),
        button =
          e.target instanceof Element &&
          !!e.target.closest('button,a,[role="treeitem"]');
      if (shortcut("commands")) {
        e.preventDefault();
        e.stopPropagation();
        setCommandQuery("");
        setDialog("commands");
        return;
      }
      if (shortcut("sidebar")) {
        e.preventDefault();
        e.stopPropagation();
        setPrefs((p) => ({ ...p, collapsed: !p.collapsed }));
        return;
      }
      if (PAGES.some(item=>shortcut("page-"+item.id))) {
        e.preventDefault();
        e.stopPropagation();
        const target = PAGES.find(item=>shortcut("page-"+item.id));
        if (target) go(target.id);
        return;
      }
      if (shortcut("settings")) {
        e.preventDefault();
        e.stopPropagation();
        go("settings");
        return;
      }
      if (shortcut("regions")) {
        e.preventDefault();
        e.stopPropagation();
        const regions = [
          document.querySelector('.sidebar nav [aria-current="page"]') ||
            document.querySelector(".sidebar nav button"),
          document.querySelector(
            '.sidebar-tree-scroll [role="treeitem"][tabindex="0"]',
          ),
          listRef.current ||
            document.querySelector(
              ".workspace-area input,.workspace-area button",
            ),
          document.querySelector(".cm-content"),
          document.querySelector('.wb-console [tabindex="0"]'),
        ].filter(
          (x, i, a) => x && x.getClientRects().length && a.indexOf(x) === i,
        );
        const focus = document.activeElement;
        const index = regions.findIndex(
          (x) =>
            x === focus ||
            x.contains(focus) ||
            (x.closest(".sidebar nav") &&
              x.closest(".sidebar nav")?.contains(focus)) ||
            (x.closest(".sidebar-tree-scroll") &&
              x.closest(".sidebar-tree-scroll")?.contains(focus)),
        );
        regions[
          (index + (e.shiftKey ? -1 : 1) + regions.length) % regions.length
        ]?.focus();
        return;
      }
      if (
        shortcut("search") &&
        !practiceId &&
        !(page === "mock" && active)
      ) {
        e.preventDefault();
        const input=document.querySelector("#tb-page-search input");input?.focus();input?.select();
        return;
      }
      if (shortcut("refresh")) {
        e.preventDefault();
        reload().then(() => notice("已刷新"));
        return;
      }
      if (e.key === "Escape") {
        if (page==='settings' && settingsTab!=='home') {e.preventDefault();setSettingsTab('home');return;}
        if (page==='settings') {e.preventDefault();go(lastWorkspacePage.current);return;}

        if (readerId) {
          e.preventDefault();
          readerSeq.current++;
          setReaderId(null);
          setReaderFull(false);
          focusList();
          return;
        }
        if (typing && e.target === searchRef.current) {
          e.preventDefault();
          setFilter({ query: "" });
          focusList();
          return;
        }
        if (practiceId) {
          e.preventDefault();
          exitPractice();
          return;
        }
        if (record && !typing) {
          e.preventDefault();
          setRecord(null);
          return;
        }
      }
      if (typing || button) return;
      if ((control || e.altKey) && !["practice","solution","favorite","listSearch","help"].some(shortcut)) return;
      if (shortcut("help")) {
        e.preventDefault();
        setPage("settings");setSettingsTab("training");
        return;
      }
      if (page === "mock" && active && /^[1-9]$/.test(e.key)) {
        const slot = active.slots[Number(e.key) - 1];
        if (slot) {
          e.preventDefault();
          setMockSlot(slot.id);
        }
        return;
      }
      if (practiceId) return;
      if (!["mine", "library"].includes(page)) return;
      if (shortcut("listSearch") || e.key === "/") {
        e.preventDefault();
        searchRef.current?.focus();
        return;
      }
      const list = listRef.current;
      if (
        !list?.contains(document.activeElement) &&
        document.activeElement !== document.body
      )
        return;
      const items = visibleRef.current,
        current = items.findIndex((r) => r.id === selectedRef.current);
      if (
        [
          "ArrowDown",
          "ArrowUp",
          "j",
          "k",
          "Home",
          "End",
          "PageDown",
          "PageUp",
        ].includes(e.key)
      ) {
        e.preventDefault();
        let index = current;
        if (e.key === "Home") index = 0;
        else if (e.key === "End") index = items.length - 1;
        else
          index += ["ArrowDown", "j"].includes(e.key)
            ? 1
            : ["ArrowUp", "k"].includes(e.key)
              ? -1
              : e.key === "PageDown"
                ? 10
                : -10;
        const nextIndex = Math.max(0, Math.min(items.length - 1, index));
        pointerPosition.current = null;
        setHoveredRow(null);
        setKeyboardSelection(true);
        if (page === "library") setLibraryPage(Math.floor(nextIndex / libraryPageSize) + 1);
        setSelected(items[nextIndex]?.id || null);
        list.focus({ preventScroll: true });
      }
      if (shortcut("practice") && selectedRef.current) {
        e.preventDefault();
        openPractice(selectedRef.current);
      }
      if (shortcut("solution") && selectedRef.current) {
        e.preventDefault();
        openSolution(selectedRef.current);
      }
      if (shortcut("favorite") && selectedRef.current) {
        e.preventDefault();
        toggleFavorite(selectedRef.current);
      }
      if (
        e.key === "Delete" &&
        selectedRef.current &&
        page === "mine"
      ) {
        e.preventDefault();
        removeTraining(selectedRef.current);
      }
    }
    window.addEventListener("keydown", keyboard, true);
    return () => window.removeEventListener("keydown", keyboard, true);
  });

  function renderRows(items) {
    return items.map((row) => (
      <tr
        key={row.id}
        data-id={row.id}
        data-selected={keyboardSelection && selected === row.id}
        aria-selected={keyboardSelection && selected === row.id}
        data-hovered={hoveredRow === row.id}
        onClick={(e) => {
          if (!e.target.closest("button,a,input,select,label,summary")) {
            setSelected(row.id);
            openPractice(row.id);
          }
        }}
      >
        <ProblemCells row={row} favorites={prefs.favorites} showPlatforms={prefs.showPlatforms} busy={busy} onTrain={id=>{setSelected(id);openPractice(id);}} onTag={filterCategory} onFavorite={toggleFavorite} onSolution={openSolution} onAddToList={id=>setListProblemIds(Array.isArray(id)?id:[id])} onRemove={removeTraining}/>
      </tr>
    ));
  }
  function renderTable(items) {
    const goalIds = new Set((workspace.goalTasks || []).map(task => task.id));
    const groupOf=row=>trainingGroup(row,goalIds);
    const groups = page === "mine" ? [
      { id: "goals", name: "今日目标", color: "accent", rows: items.filter(row => groupOf(row)==='goals') },
      ...QUEUES.map(queue => ({ ...queue, rows: items.filter(row => groupOf(row)===queue.id) })),
      { id: "practice", name: "继续练习", color: "neutral", rows: items.filter(row => groupOf(row)==='practice') },
      { id: "accepted", name: "已 AC", color: "green", rows: items.filter(row => groupOf(row)==='accepted') },
    ] : null;
    return (
      <div className="table-scroll" ref={listRef} tabIndex={0} role="region" aria-label="题目列表"
        onPointerMove={event => {
          pointerPosition.current = { x:event.clientX,y:event.clientY };
          setHoveredRow(event.target.closest('tr[data-id]')?.dataset.id || null);
          if (keyboardSelection) setKeyboardSelection(false);
        }}
        onPointerLeave={() => { pointerPosition.current=null;setHoveredRow(null); }}
        onScroll={() => {
          const position=pointerPosition.current;
          if (!position) return;
          const row=document.elementFromPoint(position.x,position.y)?.closest('tr[data-id]');
          setHoveredRow(row && listRef.current?.contains(row) ? row.dataset.id : null);
        }}>
        <table className="problem-table">
          <ProblemTableHead onSort={()=>setFilter({sort:'difficulty',desc:currentFilters.sort==='difficulty'?!currentFilters.desc:false})} sorted={currentFilters.sort==='difficulty'} descending={currentFilters.desc}/>
          <tbody>{groups ? groups.filter(group => group.rows.length).map(group => (
            <FragmentRows key={group.id} header={<tr className={"queue-heading " + group.color}><td colSpan={6}><strong>{group.name}</strong><span>{group.rows.length} 题</span></td></tr>}>
              {renderRows(group.rows)}
            </FragmentRows>
          )) : renderRows(items)}</tbody>
        </table>
        {!items.length && <Empty icon={page === "mine" && !todayMine.length ? Check : Search} title={page === "mine" && !todayMine.length ? "今天暂无训练题目" : "没有匹配的题目"} description={page === "mine" && !todayMine.length ? "到期复习会自动出现在这里，也可以去题库开始今天的练习。" : "试试减少筛选条件，或换一个关键词。"}>
          <button className="secondary" onClick={resetFilters}>清除筛选</button>
          <button className="primary" onClick={() => go("library")}>选择新的练习</button>
        </Empty>}
      </div>
    );
  }
  function toolbar() {
    return <PageSearch><label className="search-box"><Search size={17}/><input ref={searchRef} aria-label="搜索题目" value={currentFilters.query} onChange={event=>setFilter({query:event.target.value})} onKeyDown={event=>{if(['ArrowDown','Enter'].includes(event.key)){event.preventDefault();focusList();}}}/></label><SortDirection label="切换题目排序方向" descending={currentFilters.desc} onChange={desc=>setFilter({desc})}/><ProblemFilters rows={data?.rows || []} categories={categories} views={prefs.views||[]} onDeleteView={id=>setPrefs(previous=>({...previous,views:previous.views.filter(view=>view.id!==id)}))} value={currentFilters} onChange={setFilter} onReset={resetFilters} onSave={()=>{setViewName('');setDialog('saveView');}} onClear={page==='mine'?()=>setDialog('clear-training'):undefined} clearDisabled={busy||!mine.length||!!active||!!workspace.summary.pending}/>{page==='library'&&<Tooltip text={Boolean(currentFilters.query||currentFilters.category||currentFilters.result||currentFilters.catalogPath?.length)?`将筛选结果加入题单（${visible.length} 道题）`:`加入题单（${visible.length} 道题）`}><button type="button" className="icon-button" aria-label="将筛选结果加入题单" disabled={busy||!visible.length||query!==currentFilters.query} onClick={()=>setListProblemIds(visible.map(row=>row.id))}><ListPlus size={17}/></button></Tooltip>}{page==='library'&&<RandomProblem rows={visible} disabled={busy||query!==currentFilters.query} onChoose={openPractice} onError={error=>notice(error.message,'error')}/>}{currentFilters.category&&<span className="active-knowledge-filter" role="group" aria-label="当前知识点筛选"><span>{currentFilters.category.name}</span><button type="button" aria-label={`清除知识点筛选 ${currentFilters.category.name}`} onClick={()=>setFilter({category:null})}><X size={13}/></button></span>}</PageSearch>;
  }

  function renderListPage() {
    if (page === "mine" && !mine.length)
      return (
        <Empty
          icon={Target}
          title="从第一道题开始"
          description="选择一题、一场比赛，或组成自己的模拟赛。你的进度从这里积累。"
        >
          <button className="primary" onClick={() => go("library")}>
            <Library size={16} />
            去题库选题
          </button>
          <button className="secondary" onClick={() => go("mock")}>
            <Flag size={16} />
            创建模拟赛
          </button>
        </Empty>
      );
    return (
      <div className="list-page">
        {toolbar()}
        {renderTable(displayedRows)}
        {page === "library" ? <PagePagination label="题库分页" count={`共 ${visible.length} 题`} page={currentLibraryPage} pages={libraryPages} previousLabel="题库上一页" nextLabel="题库下一页" onPrevious={()=>setLibraryPage(currentLibraryPage-1)} onNext={()=>setLibraryPage(currentLibraryPage+1)}/> : <div className="list-footer"><span role="status">共 {visible.length} 题</span></div>}
      </div>
    );
  }
  function recordDetail() {
    return (
      <div className="record-detail">
        <div className="record-bar">
          <button className="secondary" onClick={() => setRecord(null)}>
            <ArrowLeft size={15} />
            所有记录
          </button>
          <h2>{record.name}</h2>
          <span>
            {record.accepted}/{record.total} AC
          </span>
          <button
            className={"secondary " + (recordOnlyPending ? "active" : "")}
            onClick={() => setRecordOnlyPending(!recordOnlyPending)}
          >
            只看未 AC
          </button>
        </div>
        <div className="record-meta">
          <span>{formatDate(record.startedAt)}</span>
          <span>限时 {record.duration} 分钟</span>
          <span>{record.status === "running" ? "进行中" : "已结束"}</span>
          {record.penalty > 0 && <span>罚时 {record.penalty} 分钟</span>}
        </div>
        <div className="record-slots scroll-panel">
          {record.slots
            .filter((slot) => !recordOnlyPending || !slot.accepted)
            .map((slot) => (
              <article className="record-slot" key={slot.id}>
                <span
                  className={"slot-letter " + (slot.accepted ? "solved" : "")}
                >
                  {slot.letter}
                </span>
                <div>
                  <strong><InlineTitle>{slot.title}</InlineTitle></strong>
                  {record.status !== "running" && <small>{slot.tags?.join(" / ")}</small>}
                </div>
                {record.status !== "running" && <Difficulty value={slot.difficulty} row={{difficulty:slot.difficulty,difficultyHidden:rows.find(row=>row.id===slot.id || row.aliasIds?.includes(slot.id))?.difficultyHidden}} />}
                <Verdict value={slot.verdict} accepted={slot.accepted} />
                <span>{slot.attempts || 0} 次提交</span>
                <button
                  className="secondary"
                  onClick={() => openPractice(slot.id)}
                >
                  {slot.accepted ? "再练一次" : "继续攻克"}
                </button>
                <IconButton
                  label={"题解 " + slot.title}
                  icon={BookOpen}
                  onClick={() => openSolution(slot.id)}
                />
              </article>
            ))}
          {record.slots.filter((slot) => !recordOnlyPending || !slot.accepted)
            .length === 0 && (
            <Empty
              icon={Trophy}
              title="这套题已经全部通过"
              description="下一步可以选择更高一档的试卷。"
            />
          )}
        </div>
      </div>
    );
  }
  function settingsPage() {
    return <PreferencesPage rows={rows} insights={insights} onTrain={openPractice} tab={settingsTab} onTab={setSettingsTab} prefs={prefs} setPrefs={setPrefs} display={display} onFullscreen={applyFullscreen} api={api} softwareUpdate={softwareUpdate} hub={hub} account={account} accountFocus={accountFocus} profileSnapshot={profileSnapshot} onProfileChanged={profileChanged} onRefresh={()=>refreshBackground(true)} onHubChanged={setHub} onError={message=>notice(message, "error")} onContent={openUpdate} onMessages={()=>setDialog("updates")} onTutorial={()=>{setTourContext('catalog');setTourOpen(true)}} onKeyboard={()=>{setPage("settings");setSettingsTab("training");}} commands={{pages:PAGES,items:commands}}/>;
  }

  const navigationPages = orderedPages(PAGES, prefs);
  const navigationEntries = navigationPages.reduce((entries, item) => {
    if (!item.group) entries.push(item);
    else if (!entries.some(entry => entry.group === item.group)) { const members = navigationPages.filter(member => member.group === item.group); entries.push({ ...item, id: "group:" + item.group, label: item.group, icon: Layers, key: "", members }); }
    return entries;
  }, []);
  const mergedPages = navigationPages.filter(item => item.group && item.group === navigationPages.find(entry => entry.id === page)?.group);
  const achievements = insights?.achievements || [], unlockedAchievements = achievements.filter(item => item.unlocked);
  const acAchievements = achievements.filter(item => /^official-\d+$/.test(item.id) && Number.isFinite(item.target)).slice().sort((a, b) => a.target - b.target);
  const highestAcAchievement = acAchievements.filter(item => item.unlocked).at(-1), nextAcAchievement = acAchievements.find(item => !item.unlocked);
  const growth = insights?.growth, growthReady = Number.isFinite(growth?.level);
  const unseenAchievements = unlockedAchievements.filter(item => !(prefs.seenAchievements || []).includes(item.id));
  function openAchievements() { setDialog("achievements"); }
  function markAchievementSeen(id) {
    setPrefs(previous => (previous.seenAchievements || []).includes(id) ? previous : {
      ...previous, seenAchievements: [...(previous.seenAchievements || []), id],
    });
  }
  const currentPage = navigationPages.find((p) => p.id === page),
    currentMockSlot =
      active?.slots.find((slot) => slot.id === mockSlot) || active?.slots[0];
  const conciseSolution = reader && briefSolution(reader.markdown, rows.find(row => row.id === readerId)?.difficulty);
  const readerPanel = readerId && (
    <aside
      className={"reader-panel " + (readerFull ? "reader-full" : "")}
      style={!readerFull ? { width: prefs.readerWidth } : undefined}
      aria-label="题解阅读"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Escape") {
          e.preventDefault();
          e.stopPropagation();
          readerSeq.current++;
          setReaderId(null);
          setReaderFull(false);
          focusList();
        }
      }}
    >
      <div
        className="reader-resizer"
        role="separator"
        aria-label="调整题解宽度"
        aria-orientation="vertical"
        tabIndex={0}
        onPointerDown={resizeReader}
        onKeyDown={(e) => {
          if (["ArrowLeft", "ArrowRight"].includes(e.key)) {
            e.preventDefault();
            setPrefs((p) => ({
              ...p,
              readerWidth: Math.max(
                340,
                Math.min(
                  900,
                  p.readerWidth + (e.key === "ArrowLeft" ? 30 : -30),
                ),
              ),
            }));
          }
        }}
      />
      <Suspense fallback={<div className="reader-content" role="status"><LoaderCircle className="spin" size={20}/></div>}><SolutionReader key={readerId} reader={reader} error={readerError} api={api} methodId={readerMethod} onMethodChange={setReaderMethod} prefs={prefs} setPrefs={setPrefs} onTrain={openPractice} fullscreen={readerFull} onFullscreen={()=>setReaderFull(!readerFull)} onClose={()=>{readerSeq.current++;setReaderId(null);setReader(null);setReaderFull(false);focusList();}}/></Suspense>
    </aside>
  );
  const beforeTodayAc = insights?.summary?.beforeTodaySolved ?? Math.max(summary.beforeTodayAccepted || 0, (insights?.summary?.totalSolved ?? summary.historicalAccepted ?? 0) - (summary.todayAccepted || 0));
  const todayAc = insights?.summary?.todaySolved ?? summary.todayAccepted ?? 0;
  return (
    <DifficultyDisplayProvider mode={prefs.difficultyDisplay}><DifficultyBoundsProvider rows={data?.rows||[]}><div
      className={"app-shell " + (prefs.collapsed ? "sidebar-collapsed " : "") + (practiceId || mockFocus ? "mock-focus practice-focus" : labFocus?"lab-focus":"")}
    >
      <SoftwareUpdateNotice update={softwareUpdate} onDetails={() => { setPage('settings'); setSettingsTab('updates'); }} />
      <aside className="sidebar">
        <div className="brand">
          <button type="button" className="brand-mark" aria-label={prefs.collapsed?"展开侧边栏":"收起侧边栏"} aria-expanded={!prefs.collapsed} onClick={()=>setPrefs(previous=>({...previous,collapsed:!previous.collapsed}))}>
            <BrandWordmark/>
          </button>

        </div>
        <nav aria-label="主导航">
          {navigationEntries.map((p) => (
            <button
              key={p.id}
              className={"nav-item " + (page === p.id || p.members?.some(member => member.id === page) ? "active" : "")}
              aria-current={page === p.id || p.members?.some(member => member.id === page) ? "page" : undefined}
              aria-label={p.label}
              aria-describedby={dueCount > 0 && (p.id === "mine" || p.members?.some(member => member.id === "mine")) ? `training-pending-${p.id}` : undefined}
              title={prefs.collapsed ? p.label + (p.key ? " · Ctrl+" + p.key : "") : undefined}
              onClick={() => go(p.members ? p.members.find(member => member.id === page)?.id || p.members[0].id : p.id)}
            >
              <p.icon size={18} />
              {!prefs.collapsed && (
                <>
                  <span>{p.label}</span>
                  {p.id === "mock" && active && <span className="live-dot" />}
                </>
              )}
              {dueCount > 0 && (p.id === "mine" || p.members?.some(member => member.id === "mine")) && <><i className="training-pending-dot" aria-hidden="true" /><span className="sr-only" id={`training-pending-${p.id}`}>有 {dueCount} 项未完成训练待办</span></>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button
            className={"nav-item " + (page === "settings" ? "active" : "")}
            aria-label="设置"
            title="设置 · Ctrl+,"
            onClick={() => go("settings")}
          >
            <Settings size={18} />
            {!prefs.collapsed && (
              <>
                <span>设置</span>
                <AccountSyncStatus />
              </>
            )}
          </button>
        </div>
      </aside>
      <main className="main-area">
        <header className={"topbar " + (practiceId || mockFocus ? "training-chrome-hidden" : "")}>
          <div id="tb-page-location" className="page-location-slot"/>
          <div id="tb-page-search" className="topbar-search-slot"/>
          <div className="topbar-actions">
            <PracticeStreak days={summary.streak || 0} completedToday={Number(todayAc)>0}/>{window.__tbAdmin&&<span className="admin-workspace-label">管理员</span>}<div className="topbar-titles"><TitleMedals titles={insights?.equippedTitles || growth?.equippedTitles || []} /></div>
            {active && page !== "mock" && (
              <button className="live-contest" onClick={() => go("mock")}>
                <Clock size={14} />
                {timerText(remainingSeconds(active, now))}
              </button>
            )}
            <button className="text-button topbar-daily-ac topbar-status-chip" aria-label={`AC：历史 ${beforeTodayAc}，今日 ${todayAc}`} onClick={()=>go('mine')}><span className="metric-label">AC</span><span className="metric-separator" aria-hidden="true">:</span><b>{beforeTodayAc}{todayAc>0&&<span className="topbar-ac-today">+{todayAc}</span>}</b></button>
            {social.snapshot?.available && <button className="text-button topbar-love-count topbar-status-chip" data-positive={Number(social.snapshot.todayLikes)>=1} aria-label={`爱心：历史 ${Math.max(0,(social.snapshot.totalLikes||0)-(social.snapshot.todayLikes||0))}，今日 ${social.snapshot.todayLikes||0}`} onClick={() => setDialog('updates')}><Heart size={18} fill="currentColor"/><span className="metric-separator" aria-hidden="true">:</span><b>{Math.max(0,(social.snapshot.totalLikes||0)-(social.snapshot.todayLikes||0))}{social.snapshot.todayLikes>0&&<span className="topbar-ac-today">+{social.snapshot.todayLikes}</span>}</b></button>}
            <ProfileBadge growth={growth} avatar={prefs.avatarData} nickname={account?.nickname || profileSnapshot?.profile?.nickname} onClick={()=>openAccounts('profile')} onAvatarClick={()=>setDialog('avatar')}/>
            <IconButton
              label="消息通知"
              icon={Bell}
              onClick={() => setDialog("updates")}
            >
              {((hub?.notifications || []).some((n) => !n.read) || social.snapshot?.unreadCount > 0) && (
                <span className="notification-dot" />
              )}
            </IconButton>

          </div>
        </header>
        <footer className={"app-statusbar " + (practiceId || mockFocus ? "training-chrome-hidden" : "")}> <Tooltip text="比赛日历"><button className="achievement-top-button contest-calendar-button" aria-label="比赛日历" onClick={()=>setDialog('contest-calendar')}><CalendarClock size={18}/>{calendar.hasUnreadToday&&<i className="notification-dot" aria-hidden="true"/>}</button></Tooltip><button className="achievement-top-button daily-task-top-button" aria-label="每日任务" onClick={() => setDialog("daily-tasks")}><CalendarDays size={17} /><small>{(insights?.dailyTasks?.tasks || []).filter(task => task.claimed).length}/{insights?.dailyTasks?.tasks?.length || 6}</small>{(insights?.dailyTasks?.tasks?.some(task => task.completed && !task.claimed)) && <i className="notification-dot" />}</button>
            <button className="achievement-top-button" aria-label="成就" onClick={openAchievements}><Medal size={17} /><small>{unlockedAchievements.length}/{achievements.length}</small>{unseenAchievements.length > 0 && <i className="notification-dot" />}</button>
{prefs.widgets && <TopbarClock />}</footer>
        {error && (
          <div className="error-banner" role="alert">
            {error}
            <button onClick={() => reload(true)}>重新读取</button>
          </div>
        )}
        {!practiceId && mergedPages.length > 1 && <div className="merged-page-tabs" role="tablist" aria-label={`组合页面 ${currentPage?.group}`}>{mergedPages.map(item => <button key={item.id} role="tab" aria-selected={page === item.id} className={page === item.id ? "active" : ""} onClick={() => go(item.id)}><item.icon size={15} />{item.label}{item.id === "mine" && dueCount > 0 && <i className="training-tab-dot" role="img" aria-label="有未完成训练待办" />}</button>)}</div>}
        <div data-page={practiceId ? "practice" : page} className={"workspace-area " + (practiceId ? "practicing" : "")} style={{ '--page-opacity': `var(--opacity-${practiceId ? 'mock' : page}, var(--panel-opacity))` }}>
          <Suspense fallback={<div className="loading-screen" role="status"><LoaderCircle size={27} className="spin" /><p>正在载入</p></div>}>
          {loading ? (
            <div className="loading-screen">
              <LoaderCircle size={27} className="spin" />
              <p>正在打开训练工作台</p>
            </div>
          ) : practiceId ? (
            <Workbench
              key={"practice:" + practiceId}
              shortcuts={prefs.shortcuts}
              problemId={practiceId}
              preparedProblem={practicePrefetch.current?.id===practiceId?practicePrefetch.current.promise:null}
              reviewTask={practiceReview}
              contest={null}
              api={api}
              onProgress={progressChanged}
              onExit={exitPractice}
              onSolution={openSolution}
              solutionOpen={readerId === practiceId}
              solutionMethodId={readerMethod||reader?.primaryMethod||reader?.methods?.[0]?.id}
              onNext={nextPractice}
            />
          ) : ["mine", "library"].includes(page) ? (
            page === "mine" ? <div className="training-workspace">{renderListPage()}</div> : renderListPage()
          ) : page === "mock" ? (
            <div className="mock-page">{record ? recordDetail() : <>{active && mockTab === "create" ? (
              <div className="contest-player">
                {currentMockSlot && (
                  <Workbench
                    key={active.id + ":" + currentMockSlot.id}
                    problemId={currentMockSlot.id}
                    shortcuts={prefs.shortcuts}
              contest={active}
                    api={api}
                    onProgress={applyWorkspace}
                    onExit={() => go("mine")}
                    onSolution={null}
                    headerStart={<MockProblemPicker
                      shortcuts={prefs.shortcuts}
              contest={active}
                      currentId={currentMockSlot.id}
                      onSelect={(id) => {
                        setMockSlot(id);
                        requestAnimationFrame(() => document.querySelector('.mock-problem-trigger')?.focus());
                      }}
                      onHistory={() => {
                        setMockTab("history");
                        requestAnimationFrame(() => document.getElementById('mock-history-heading')?.focus());
                      }}
                    />}
                    headerEnd={<>
                      <span className={"mock-timer " + (remainingSeconds(active, now) < 600 ? "urgent" : "")} role="timer" aria-label="比赛剩余时间">
                        <Clock size={14} aria-hidden="true" />
                        {timerText(remainingSeconds(active, now))}
                      </span>
                      <button type="button" className="wb-button finish-contest" onClick={event => setFinishAnchor(event.currentTarget)}>
                        结束比赛
                      </button>
                    </>}
                    onNext={() => {
                      const index = active.slots.findIndex(
                        (s) => s.id === currentMockSlot.id,
                      );
                      setMockSlot(
                        active.slots[(index + 1) % active.slots.length].id,
                      );
                    }}
                  />
                )}
              </div>
            ) : <>{active ? <div className="mock-resume-row"><button className="secondary" onClick={()=>setMockTab("create")}><Play size={15}/>继续比赛</button></div> : (
              <MockSetup
                historyQuery={mockHistoryQuery}
                onHistoryQuery={setMockHistoryQuery}
                onPreviewChange={setMockPreview}
                api={api}
                activeContest={active}
                onResume={() => go("mock")}
                categories={categories}
                platforms={[...new Set(rows.map(row => row.platform).filter(Boolean))]}
                onStarted={startedMock}
                onError={notice}
              />
            )}{!mockPreview&&<MockHistory embedded query={mockHistoryQuery} contests={workspace.contests} onDelete={async body => { const answer = await api("contests/delete", body); applyWorkspace(answer.workspace); notice(`已删除 ${answer.deleted} 场模拟赛记录`); }} onSelect={openRecord} onResume={contest=>{setMockTab("create");setMockSlot(contest.slots[0]?.id);}} onCreate={()=>{setMockTab("create");document.querySelector('.mock-create')?.scrollIntoView({block:'start'});}}/>}</>}</>}</div>
          ) : page === "records" ? (
            <SubmissionRecords api={api} revision={workspace.summary?.attempts} rows={rows} onOpenProblem={openPractice} onSelect={(submission) => { setSelectedSubmission(submission); setDialog("submission"); }} />
          ) : page === "competitions" ? (
            <CompetitionPage
              rows={rows}
              workspace={workspace}
              hub={hub}
              onTrain={openPractice}
              initialContest={calendarContest}
              onBack={()=>setCalendarContest(null)}
              onJoin={startOriginalContest}
              onStartReproduction={startReproduction}
            />
          ) : page === "growth" ? (
            <GrowthPage
              categories={categories}
              rows={data?.rows||[]}
              avatarData={prefs.avatarData}
              onAvatar={()=>setDialog('avatar')}
              onRankings={() => go("rankings")}
              api={api}
              onGoalsChanged={() => api("workspace").then(applyWorkspace)}
              insights={insights}
              hub={hub}
              goalOverview={workspace.goals}
              account={account}
              profile={profileSnapshot?.profile}
              profileSnapshot={profileSnapshot}
              accountFocus={accountFocus}
              onProfileChanged={profileChanged}
              onHubChanged={setHub}
              onError={(message) => notice(message, 'error')}
              onTrain={openPractice}
              onTopic={(node) => filterCategory(node, "library")}
              onSync={() =>
                api("hub/sync", {})
                  .then(setHub)
                  .catch((e) => notice(e.message, "error"))
              }
              onAccounts={() => openAccounts('connections')}
              onAchievements={openAchievements}
            />
          ) : page === "goals" ? (
            <GoalsPanel api={api} overview={workspace.goals} onChanged={() => reload()} />
          ) : page === "activity" ? (
            <ActivityPage insights={insights} onTrain={openPractice} />
          ) : page === "training-lists" ? (
            <TrainingListsPage rows={rows} api={api} onTrain={openPractice} visit={trainingListsVisit.current} pageSize={prefs.libraryPageSize} busy={busy} prefs={prefs} onTag={filterCategory} onFavorite={toggleFavorite} onSolution={openSolution} onAddToList={id=>setListProblemIds(Array.isArray(id)?id:[id])} onRemove={removeTraining}/>
          ) : page === "templates" ? (
            <TemplatesPage api={api} shortcuts={prefs.shortcuts} visit={templatesVisit.current}/>
          ) : page === "paths" ? (
            <LearningPathsPage rows={rows} api={api} prefs={prefs} setPrefs={setPrefs} onTrain={openPractice} lockedProblems={active?.slots || []} visit={labVisit.current}/>
          ) : page === "lectures" ? (
            <LecturesPanel prefs={prefs} setPrefs={setPrefs} api={api} visit={lecturesVisit.current} initialLecture={lectureId} categories={categories} onTrain={openPractice} onError={(message) => notice(message, "error")} />
          ) : page === "rankings" ? (
            <RankingsPage socialState={social} avatarData={prefs.avatarData} ownGrowth={growth} api={api} onConfigure={() => {if(window.__tbAdmin){setPage('settings');setSettingsTab('admin')}else openAccounts()}} onError={(message) => notice(message, "error")} />
          ) : (
            settingsPage()
          )}
          </Suspense>
          <Suspense fallback={<div className="loading-small" role="status"><LoaderCircle className="spin" size={20} /></div>}>{readerPanel}</Suspense>
        </div>
      </main>
      {toast && (
        <div className={"toast " + toast.type} role="status">
          {toast.type === "success" ? (
            <Trophy size={17} />
          ) : toast.type === "error" ? (
            <X size={16} />
          ) : (
            <Check size={16} />
          )}
          <span>{toast.message}</span>
          {toast.action && (
            <button onClick={toast.action.run}>{toast.action.label}</button>
          )}
        </div>
      )}
      {dialog === "daily-tasks" && <Modal title="每日任务" onClose={() => setDialog(null)} wide><DailyTasks dailyTasks={insights?.dailyTasks} onClaim={async (id, date) => { try { const result = await api("daily-tasks/claim", { id, date }); backgroundSeq.current++; setInsights(previous => ({ ...previous, dailyTasks: result.dailyTasks })); notice("经验已领取", "success"); void refreshBackground(true); } catch (issue) { notice(issue.message, "error"); throw issue; } }} /></Modal>}
      {dialog === 'contest-calendar' && <Modal title="比赛日历" onClose={()=>setDialog(null)} wide><ContestCalendar calendar={calendar} onOpen={async contest=>{await reload();setCalendarContest(contest.import?.title||contest.title);setDialog(null);go("competitions");}}/></Modal>}
      {dialog === "avatar" && <Modal title="修改头像" onClose={()=>setDialog(null)}><Suspense fallback={<p role="status">正在读取…</p>}><AvatarSettings prefs={prefs} setPrefs={setPrefs} onError={message=>notice(message,"error")}/></Suspense></Modal>}
      {tourOpen && <Suspense fallback={null}><Onboarding initialGuide={tourContext} practiceId={practiceId||(mockFocus?currentMockSlot?.id:null)} onComplete={finishOnboarding} onNavigate={(target,tab)=>{go(target);if(target==="settings")setSettingsTab(tab||"home");}}/></Suspense>}
      {dialog === "achievements" && <Modal title={`成就 · ${unlockedAchievements.length}/${achievements.length}`} onClose={() => setDialog(null)} wide><AchievementPanel achievements={achievements} newIds={unseenAchievements.map(item => item.id)} onSeen={markAchievementSeen} /></Modal>}
      {dialog === "submission" && selectedSubmission && <Modal title={selectedSubmission.title + " · 历史提交"} onClose={() => setDialog(null)} wide footer={<button className="primary" onClick={() => { setDialog(null); openPractice(selectedSubmission.problemId); }}><Play size={14} />继续练习</button>}><div className="submission-detail-meta"><Verdict value={selectedSubmission.verdict} /><span>{formatDate(selectedSubmission.submittedAt)}</span><span>{selectedSubmission.contestName}</span><button className="secondary" disabled={!selectedSubmission.code} onClick={() => copy(selectedSubmission.code)}><Copy size={14} />复制本次代码</button></div><pre className="submission-source"><code>{selectedSubmission.code || "这条记录没有保存代码。"}</code></pre>{selectedSubmission.message && <p className="submission-message">{selectedSubmission.message}</p>}</Modal>}
      {dialog === "updates" && (
        <Modal title="消息与更新" onClose={() => setDialog(null)} wide>
          <SocialNotifications social={social} api={api}/>
          <UpdatePanel notificationsOnly
            softwareState={softwareUpdate.state}
            onContent={openUpdate}
            hub={hub}
            api={api}
            onChanged={value=>{backgroundSeq.current++;setHub(value);}}
            onError={(message) => notice(message, "error")}
          />
        </Modal>
      )}
      {dialog === "summary" && (
        <Modal title="你的训练概览" onClose={() => setDialog(null)}>
          <div className="summary-score">
            <Trophy size={27} />
            <strong>
              {passedCount}
              <small> / {totalCount}</small>
            </strong>
            <span className={highestAcAchievement ? 'summary-earned-achievement' : ''}>{highestAcAchievement && <Trophy size={17} />}{!insights ? "成长与成就数据读取中" : highestAcAchievement?.name || "开始训练"}</span>
          </div>
          <div className="summary-grid">
            <div>
              <strong>{num(summary.attempts)}</strong>
              <span>代码提交</span>
            </div>
            <div>
              <strong>
                {
                  workspace.contests.filter((c) => c.status === "finished")
                    .length
                }
              </strong>
              <span>完成模拟赛</span>
            </div>
          </div>
          <p className="summary-description">
            题库 {rows.filter(row => !row.catalogHidden).length}{" "}
            题可供选择。个人分母只包含主动加入的单题、比赛和模拟赛，同题只计一次。
          </p>
          <div className="milestones">
            {nextAcAchievement ? <div className="next-ac-milestone"><Trophy size={16} /><span>下个成就 · {nextAcAchievement.name}</span><small>{num(nextAcAchievement.progress)} / {num(nextAcAchievement.target)}</small>{nextAcAchievement.rewardTitle ? <b>称号 · {nextAcAchievement.rewardTitle.name}</b> : nextAcAchievement.rewardXp > 0 && <b>+{num(nextAcAchievement.rewardXp)} XP</b>}</div> : <div>{insights ? acAchievements.length ? "全部 AC 成就已达成" : "AC 成就正在准备" : "正在读取 AC 成就"}</div>}
          </div>
          {growth?.ranked?.tierRequirements?.length > 0 && <details className="rank-requirements"><summary>段位要求</summary><p>{growth.ranked.rules}</p><table aria-label="段位能力分要求"><thead><tr><th>段位</th><th>最低能力分</th></tr></thead><tbody>{growth.ranked.tierRequirements.map(tier=><tr key={tier.badge}><td><span className={`rank-requirement-tier ${tier.badge}`}><TierIcon badge={tier.badge} size={16}/>{tier.tier}</span></td><td>{num(tier.minAbilityScore)}</td></tr>)}</tbody></table></details>}
        </Modal>
      )}
      {dialog === 'clear-training' && <Modal title="清空我的训练" onClose={() => setDialog(null)} footer={<><button className="secondary" onClick={() => setDialog(null)}>取消</button><button className="primary" disabled={busy || !!active} onClick={async () => { setBusy(true); try { const result = await api('training/clear', {}); applyWorkspace(result.workspace); setDialog(null); notice(`已清空 ${result.cleared} 道训练题，代码与提交记录已保留`, 'success'); } catch (issue) { notice(issue.message, 'error'); } finally { setBusy(false); } }}>确认清空 {mine.length} 道训练题</button></>}><p>将全部 {mine.length} 道题从训练和待办中移除，包括未在今日列表显示的题目。保留全部代码、草稿、提交历史、身份和目标计划；可以从题库重新加入。</p></Modal>}
      {dialog === "help" && (
        <Modal title="键盘操作" onClose={() => setDialog(null)} wide>
          <div className="shortcut-grid">
            <section>
              <h3>工作台</h3>
              {[
                [
                  "Ctrl+1 … 9",
                  "训练 / 题库 / 待办 / 比赛 / 模拟赛 / 记录 / 成长 / 活动 / 从零讲",
                ],
                ["Ctrl+B", "收起或展开左侧栏"],
                ["Ctrl+K", "命令面板"],
                ["F6 / Shift+F6", "切换导航、知识清单、主区与代码焦点"],
                ["Ctrl+0 / Ctrl+,", "设置"],
                ["F 或 Ctrl+F", "搜索当前列表"],
                ["Esc", "关闭题解、清空搜索或返回"],
                ["?", "打开这张键位表"],
              ].map(([key, action]) => (
                <div key={key}>
                  <kbd>{key}</kbd>
                  <span>{action}</span>
                </div>
              ))}
            </section>
            <section>
              <h3>选题与知识树</h3>
              {[
                ["↑ ↓ / J K", "选择上一题 / 下一题"],
                ["Home / End", "跳到首题 / 末题"],
                ["PageUp / PageDown", "移动十题"],
                ["Enter", "开始练习所选题"],
                ["U / S", "查看题解 / 切换收藏"],
                ["Delete", "取消所选训练，保留历史记录"],
                ["树中 → / ←", "展开分支 / 收起或返回上层"],
                ["Tab / Shift+Tab", "切换按钮与输入框"],
              ].map(([key, action]) => (
                <div key={key}>
                  <kbd>{key}</kbd>
                  <span>{action}</span>
                </div>
              ))}
            </section>
            <section>
              <h3>代码与模拟赛</h3>
              {[
                ["Ctrl+Enter", "本地评测"],
                ["Ctrl+Shift+Enter", "在主窗口提交到官方"],
                ["Ctrl+R", "运行样例 / 自定义输入"],
                ["Ctrl+S", "保存当前代码"],
                ["Tab / Shift+Tab", "缩进 / 取消缩进"],
                ["Alt+1 / Alt+2", "聚焦题面 / 代码"],
                ["1 … 9", "比赛中切题（编辑时不触发）"],
              ].map(([key, action]) => (
                <div key={key}>
                  <kbd>{key}</kbd>
                  <span>{action}</span>
                </div>
              ))}
            </section>
          </div>
          <p className="help-note">
            结果由提交代码自动生成。列表中的 1–6
            不再手动改状态，输入框与按钮保留自己的按键行为。
          </p>
        </Modal>
      )}
      {dialog === "commands" && (
        <Modal title="快捷操作" onClose={() => setDialog(null)}>
          <div className="command-search">
            <Search size={17} />
            <input
              autoFocus
              aria-label="搜索快捷操作"
              placeholder="输入要去的地方或操作…"
              value={commandQuery}
              onChange={(e) => setCommandQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  const command = commands.find((c) =>
                    c.name.includes(commandQuery),
                  );
                  if (command) {
                    setDialog(null);
                    requestAnimationFrame(() => command.action());
                  }
                }
              }}
            />
          </div>
          <div className="command-list">
            {commands
              .filter((c) => c.name.includes(commandQuery))
              .map((command) => (
                <button
                  key={command.name}
                  onClick={() => {
                    setDialog(null);
                    requestAnimationFrame(() => command.action());
                  }}
                >
                  <span>{command.name}</span>
                  {command.detail && <kbd>{command.detail}</kbd>}
                  <ChevronRight size={14} />
                </button>
              ))}
          </div>
        </Modal>
      )}
      {dialog === "saveView" && (
        <Modal
          title="保存常用筛选"
          onClose={() => setDialog(null)}
          footer={
            <button
              className="primary"
              disabled={!viewName.trim()}
              onClick={() => {
                setPrefs((p) => ({
                  ...p,
                  views: [
                    ...p.views,
                    {
                      id: String(Date.now()),
                      name: viewName.trim(),
                      filters: currentFilters,
                    },
                  ],
                }));
                setDialog(null);
                notice("已保存筛选");
              }}
            >
              保存筛选
            </button>
          }
        >
          <label className="modal-field">
            筛选名称
            <input
              aria-label="筛选名称"
              value={viewName}
              onChange={(e) => setViewName(e.target.value)}
              maxLength={40}
            />
          </label>
        </Modal>
      )}
      {listProblemIds&&<AddToTrainingLists problemIds={listProblemIds} api={api} onClose={()=>setListProblemIds(null)} onSave={()=>{delete trainingListsVisit.current.content;setListProblemIds(null);notice("已加入题单","success");}}/>}
      {finishAnchor && active && <PopConfirm anchor={finishAnchor} title="结束这场比赛？" label="结束比赛确认" busy={busy} cancelLabel="继续比赛" confirmLabel="结束并复盘" busyLabel="正在处理…" confirmTone="primary" onCancel={()=>setFinishAnchor(null)} onConfirm={()=>finishMock(false)} extraActions={<Tooltip text="撤销本场训练安排，保留草稿及真实原站提交"><button type="button" className="danger" disabled={busy} onClick={()=>finishMock(true)}>取消比赛</button></Tooltip>}/>}

    </div></DifficultyBoundsProvider></DifficultyDisplayProvider>
  );

}
function FragmentRows({ header, children }) {
  return (
    <>
      {header}
      {children}
    </>
  );
}
