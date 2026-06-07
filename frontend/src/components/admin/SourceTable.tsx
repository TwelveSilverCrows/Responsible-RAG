'use client';

import { useState, useMemo, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  FileCode,
  Mic,
  Globe,
  Youtube,
  MoreHorizontal,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Eye,
  Pencil,
  Trash2,
  Plus,
} from 'lucide-react';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { ProcessingStatus } from '@/components/admin/ProcessingStatus';
import type { Source, SourceType, SourceStatus } from '@/types/source';
import { SOURCE_TYPE_CONFIG } from '@/types/source';
import { format } from 'date-fns';

const typeIcons: Record<SourceType, React.ElementType> = {
  pdf: FileText,
  text: FileCode,
  audio: Mic,
  webpage: Globe,
  youtube: Youtube,
};

type SortField = 'title' | 'type' | 'publicationDate' | 'createdAt';
type SortDir = 'asc' | 'desc';

const ITEMS_PER_PAGE = 10;

interface SourceTableProps {
  sources: Source[];
}

export function SourceTable({ sources }: SourceTableProps) {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('createdAt');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Filter and sort
  const filtered = useMemo(() => {
    let result = [...sources];

    // Search
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (s) =>
          s.title.toLowerCase().includes(q) ||
          s.authors.some((a) => a.toLowerCase().includes(q))
      );
    }

    // Type filter
    if (typeFilter !== 'all') {
      result = result.filter((s) => s.type === typeFilter);
    }

    // Status filter
    if (statusFilter !== 'all') {
      result = result.filter((s) => s.status === statusFilter);
    }

    // Sort
    result.sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case 'title':
          cmp = a.title.localeCompare(b.title);
          break;
        case 'type':
          cmp = a.type.localeCompare(b.type);
          break;
        case 'publicationDate':
          cmp = (a.publicationDate || '').localeCompare(b.publicationDate || '');
          break;
        case 'createdAt':
          cmp = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
          break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });

    return result;
  }, [sources, search, typeFilter, statusFilter, sortField, sortDir]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE));
  const currentPage = Math.min(page, totalPages);
  const paged = filtered.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const toggleSort = useCallback(
    (field: SortField) => {
      if (sortField === field) {
        setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
      } else {
        setSortField(field);
        setSortDir('asc');
      }
    },
    [sortField]
  );

  const renderSortIcon = (field: SortField) => {
    if (sortField !== field) return <ArrowUpDown className="w-3 h-3 ml-1 opacity-40" />;
    return sortDir === 'asc' ? (
      <ArrowUp className="w-3 h-3 ml-1" />
    ) : (
      <ArrowDown className="w-3 h-3 ml-1" />
    );
  };

  const allSelected =
    paged.length > 0 && paged.every((s) => selectedIds.has(s.id));
  const someSelected = paged.some((s) => selectedIds.has(s.id)) && !allSelected;

  const toggleAll = () => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(paged.map((s) => s.id)));
    }
  };

  const toggleOne = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleBulkDelete = () => {
    // In a real app, this would call an API
    setSelectedIds(new Set());
    setDeleteDialogOpen(false);
  };

  const handleRetry = (id: string) => {
    // Mock retry — in a real app, this would call an API
    void id;
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div className="relative flex-1 w-full sm:max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by title or author..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="pl-9"
          />
        </div>
        <Select
          value={typeFilter}
          onValueChange={(v) => {
            setTypeFilter(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="All types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            {Object.entries(SOURCE_TYPE_CONFIG).map(([key, cfg]) => (
              <SelectItem key={key} value={key}>
                {cfg.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={statusFilter}
          onValueChange={(v) => {
            setStatusFilter(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="queued">Queued</SelectItem>
            <SelectItem value="processing">Processing</SelectItem>
            <SelectItem value="indexed">Indexed</SelectItem>
            <SelectItem value="error">Error</SelectItem>
          </SelectContent>
        </Select>
        {selectedIds.size > 0 && (
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setDeleteDialogOpen(true)}
          >
            <Trash2 className="w-4 h-4 mr-1" />
            Delete {selectedIds.size}
          </Button>
        )}
      </div>

      {/* Table */}
      {paged.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
            <FileText className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-1">No sources found</h3>
          <p className="text-sm text-muted-foreground mb-4">
            {search || typeFilter !== 'all' || statusFilter !== 'all'
              ? 'Try adjusting your filters or search terms.'
              : 'Start building your knowledge base by adding your first source.'}
          </p>
          {!search && typeFilter === 'all' && statusFilter === 'all' && (
            <Button asChild>
              <Link to="/admin/sources/new">
                <Plus className="w-4 h-4 mr-2" />
                Add your first source
              </Link>
            </Button>
          )}
        </div>
      ) : (
        <>
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox
                      checked={allSelected}
                      ref={(el) => {
                        if (el) {
                          (el as unknown as HTMLButtonElement).dataset.state = someSelected
                            ? 'indeterminate'
                            : allSelected
                              ? 'checked'
                              : 'unchecked';
                        }
                      }}
                      onCheckedChange={toggleAll}
                      aria-label="Select all"
                    />
                  </TableHead>
                  <TableHead>
                    <button
                      className="flex items-center gap-0.5 hover:text-foreground transition-colors"
                      onClick={() => toggleSort('title')}
                    >
                      Title {renderSortIcon('title')}
                    </button>
                  </TableHead>
                  <TableHead>
                    <button
                      className="flex items-center gap-0.5 hover:text-foreground transition-colors"
                      onClick={() => toggleSort('type')}
                    >
                      Type {renderSortIcon('type')}
                    </button>
                  </TableHead>
                  <TableHead className="hidden md:table-cell">Authors</TableHead>
                  <TableHead className="hidden lg:table-cell">
                    <button
                      className="flex items-center gap-0.5 hover:text-foreground transition-colors"
                      onClick={() => toggleSort('publicationDate')}
                    >
                      Published {renderSortIcon('publicationDate')}
                    </button>
                  </TableHead>
                  <TableHead className="hidden lg:table-cell">
                    <button
                      className="flex items-center gap-0.5 hover:text-foreground transition-colors"
                      onClick={() => toggleSort('createdAt')}
                    >
                      Added {renderSortIcon('createdAt')}
                    </button>
                  </TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-10" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {paged.map((source) => {
                  const TypeIcon = typeIcons[source.type];
                  const typeConfig = SOURCE_TYPE_CONFIG[source.type];
                  return (
                    <TableRow
                      key={source.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/admin/sources/${source.id}`)}
                    >
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <Checkbox
                          checked={selectedIds.has(source.id)}
                          onCheckedChange={() => toggleOne(source.id)}
                          aria-label={`Select ${source.title}`}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 min-w-0">
                          <TypeIcon className={`w-4 h-4 flex-shrink-0 ${typeConfig.color}`} />
                          <span className="font-medium truncate max-w-[200px] lg:max-w-[300px]">
                            {source.title}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-xs">
                          {typeConfig.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        <span className="text-sm text-muted-foreground truncate max-w-[180px] block">
                          {source.authors.join(', ')}
                        </span>
                      </TableCell>
                      <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                        {source.publicationDate
                          ? format(new Date(source.publicationDate), 'MMM d, yyyy')
                          : '—'}
                      </TableCell>
                      <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                        {format(new Date(source.createdAt), 'MMM d, yyyy')}
                      </TableCell>
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <ProcessingStatus
                          status={source.status}
                          indexedAt={source.indexedAt}
                          errorMessage={source.errorMessage}
                          onRetry={
                            source.status === 'error'
                              ? () => handleRetry(source.id)
                              : undefined
                          }
                        />
                      </TableCell>
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="w-4 h-4" />
                              <span className="sr-only">Actions</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() => navigate(`/admin/sources/${source.id}`)}
                            >
                              <Eye className="w-4 h-4 mr-2" /> View
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => navigate(`/admin/sources/${source.id}`)}
                            >
                              <Pencil className="w-4 h-4 mr-2" /> Edit
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-destructive focus:text-destructive">
                              <Trash2 className="w-4 h-4 mr-2" /> Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1}–
              {Math.min(currentPage * ITEMS_PER_PAGE, filtered.length)} of{' '}
              {filtered.length} sources
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}

      {/* Bulk delete dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {selectedIds.size} source(s)?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently remove the selected sources from the knowledge base.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleBulkDelete} className="bg-destructive text-white hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
