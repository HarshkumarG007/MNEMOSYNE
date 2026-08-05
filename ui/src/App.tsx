import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  UploadCloud, 
  Search, 
  Database, 
  CheckCircle2, 
  AlertCircle,
  Loader2,
  File
} from 'lucide-react';

const API_URL = 'http://localhost:8000/api';

// Types
interface EntityResult {
  id: string;
  name: string;
  type: string;
  evidence_hashes: string[];
}

interface IngestResponse {
  evidence_hash: string;
  mime_type: string;
  entity_count: number;
}

function App() {
  // Ingestion State
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<EntityResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  // Search Debounce
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchQuery.trim().length >= 2) {
        performSearch(searchQuery);
      } else if (searchQuery.trim().length === 0) {
        setResults([]);
        setHasSearched(false);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  const performSearch = async (query: string) => {
    setIsSearching(true);
    try {
      const response = await axios.get<EntityResult[]>(`${API_URL}/search`, {
        params: { q: query }
      });
      setResults(response.data);
      setHasSearched(true);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  // Drag and Drop Handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await handleFileUpload(e.target.files[0]);
    }
    // Reset input so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    setUploadStatus(null);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post<IngestResponse>(`${API_URL}/ingest`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setUploadStatus({
        type: 'success',
        message: `Successfully ingested "${file.name}". Extracted ${response.data.entity_count} entities.`
      });
    } catch (error: any) {
      console.error('Upload failed:', error);
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to ingest file.'
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <h1>MNEMOSYNE</h1>
        <p>Enterprise Knowledge Graph Intelligence</p>
      </header>

      <main style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
        
        {/* Search Section */}
        <section className="panel">
          <div className="search-container">
            <Search className="search-icon" />
            <input 
              type="text" 
              className="search-input"
              placeholder="Search entities (e.g. organizations, people)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {isSearching && (
              <Loader2 className="spinner" style={{ position: 'absolute', right: '1.25rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
            )}
          </div>

          {/* Results Area */}
          {(hasSearched || results.length > 0) && (
            <div className="results-grid">
              {results.length === 0 && !isSearching ? (
                <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                  No entities found matching "{searchQuery}"
                </div>
              ) : (
                results.map((entity, idx) => (
                  <div key={`${entity.id}-${idx}`} className="result-card" style={{ animationDelay: `${idx * 0.05}s` }}>
                    <div className="result-header">
                      <span className="result-name">{entity.name}</span>
                      <span className={`result-type ${entity.type}`}>{entity.type}</span>
                    </div>
                    <div className="result-meta">
                      <File size={16} />
                      <span>Found in {entity.evidence_hashes.length} document{entity.evidence_hashes.length !== 1 ? 's' : ''}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </section>

        {/* Ingestion Section */}
        <section className="panel">
          <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.5rem', fontWeight: 600 }}>
            <Database size={24} color="var(--primary-color)" />
            Ingest Knowledge
          </h2>
          
          <div 
            className={`dropzone ${isDragging ? 'active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              type="file" 
              className="hidden-input" 
              ref={fileInputRef}
              onChange={handleFileSelect}
            />
            
            {isUploading ? (
              <Loader2 size={48} className="dropzone-icon spinner" />
            ) : (
              <UploadCloud className="dropzone-icon" />
            )}
            
            <div>
              <div className="dropzone-text">
                {isUploading ? 'Processing Document...' : 'Click to upload or drag and drop'}
              </div>
              <div className="dropzone-subtext">
                Supports TXT, PDF, DOCX (Extracts Persons & Organizations automatically)
              </div>
            </div>
          </div>

          {/* Upload Status Toast */}
          {uploadStatus && (
            <div className={`status-message ${uploadStatus.type}`}>
              {uploadStatus.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
              <span>{uploadStatus.message}</span>
            </div>
          )}
        </section>

      </main>
    </div>
  );
}

export default App;
