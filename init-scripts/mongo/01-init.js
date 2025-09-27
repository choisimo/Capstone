// MongoDB 초기화 스크립트
// OSINT 데이터 저장용

// osint_data 데이터베이스 사용
db = db.getSiblingDB('osint_data');

// 컬렉션 생성
db.createCollection('raw_data');
db.createCollection('processed_data');
db.createCollection('source_metadata');
db.createCollection('crawl_history');

// 인덱스 생성
db.raw_data.createIndex({ 'source': 1, 'collected_at': -1 });
db.raw_data.createIndex({ 'url': 1 }, { unique: true });
db.raw_data.createIndex({ 'content': 'text' });

db.processed_data.createIndex({ 'processed_at': -1 });
db.processed_data.createIndex({ 'relevance_score': -1 });
db.processed_data.createIndex({ 'keywords': 1 });

db.source_metadata.createIndex({ 'source_type': 1 });
db.source_metadata.createIndex({ 'last_updated': -1 });

db.crawl_history.createIndex({ 'crawled_at': -1 });
db.crawl_history.createIndex({ 'status': 1 });

// 초기 소스 메타데이터
db.source_metadata.insertMany([
    {
        source_type: 'news',
        name: '네이버 뉴스',
        config: {
            base_url: 'https://news.naver.com',
            crawl_interval: 3600,
            max_pages: 10,
            selectors: {
                title: '.news_tit',
                content: '.news_cnt_detail_wrap',
                date: '.sponsor .txt_info'
            }
        },
        last_updated: new Date()
    },
    {
        source_type: 'community',
        name: '클리앙',
        config: {
            base_url: 'https://www.clien.net',
            crawl_interval: 1800,
            max_pages: 5,
            selectors: {
                title: '.subject_fixed',
                content: '.post_content',
                author: '.nickname'
            }
        },
        last_updated: new Date()
    },
    {
        source_type: 'rss',
        name: '구글 뉴스 RSS',
        config: {
            feed_url: 'https://news.google.com/rss/search?q=국민연금&hl=ko&gl=KR&ceid=KR:ko',
            crawl_interval: 1800,
            max_items: 50
        },
        last_updated: new Date()
    }
]);

// 크롤링 히스토리 샘플
db.crawl_history.insertOne({
    source: '네이버 뉴스',
    crawled_at: new Date(),
    status: 'initialized',
    items_collected: 0,
    duration_ms: 0,
    errors: []
});

print('MongoDB 초기화 완료');
print('데이터베이스: osint_data');
print('컬렉션: raw_data, processed_data, source_metadata, crawl_history');
print('인덱스 생성 완료');
