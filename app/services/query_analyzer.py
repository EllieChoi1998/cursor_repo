"""
Query analysis service - Handles query parsing and command type detection
"""


class QueryAnalyzer:
    """쿼리 분석 서비스"""
    
    # 데이터 타입별 지원되는 명령어
    SUPPORTED_COMMANDS = {
        'pcm': {
            'trend': ['trend', '트렌드', '차트', '그래프', '분석'],
            'commonality': ['commonality', '커먼', '공통', '분석'],
            'point': ['point', '포인트', 'site', '사이트']
        },
        'inline': {
            'analysis': ['analysis', '분석', '성능', '모니터링'],
            'performance': ['performance', '성능', '측정', '평가']
        },
        'rag': {
            'search': ['search', '검색', '찾기', '조회'],
            'summary': ['summary', '요약', '정리', '개요']
        }
    }

    @classmethod
    def analyze_query_with_choice(cls, choice: str, message: str) -> tuple[str, str, str]:
        """
        choice와 메시지를 함께 분석하여 어떤 타입의 처리가 필요한지 결정
        choice가 우선적으로 고려됨
        Returns: (data_type, command_type, error_message)
        """
        message_lower = message.lower().strip()
        choice_lower = choice.lower().strip() if choice else ""
        
        # 빈 메시지 체크
        if not message_lower:
            return "", "", "메시지를 입력해주세요."
        
        # choice가 'pcm'인 경우
        if choice_lower == 'pcm':
            return cls.analyze_pcm_query(message_lower)
        
        # choice가 'inline'인 경우
        elif choice_lower == 'inline':
            return cls.analyze_inline_query(message_lower)
        
        # choice가 'rag'인 경우
        elif choice_lower == 'rag':
            return cls.analyze_rag_query(message_lower)
        
        # choice가 없거나 인식되지 않은 경우 기존 analyze_query 로직 사용
        else:
            return cls.analyze_query(message_lower)

    @classmethod
    def analyze_pcm_query(cls, message_lower: str) -> tuple[str, str, str]:
        """PCM choice에 대한 메시지 분석"""
        # Two Tables 키워드 우선 검사 (PCM choice + 'two' 메시지)
        if 'two' in message_lower:
            # 테스트 시나리오 체크
            if 'empty' in message_lower:
                if 'lot' in message_lower and 'pe' not in message_lower:
                    return 'two', 'two_tables_empty_lot', ""
                elif 'pe' in message_lower and 'lot' not in message_lower:
                    return 'two', 'two_tables_empty_pe', ""
                else:
                    return 'two', 'two_tables_empty_both', ""
            return 'two', 'two_tables', ""
        
        # sameness_to_trend, commonality_to_trend 키워드 검사 (가장 구체적인 키워드부터 먼저 검사)
        elif 'sameness_to_trend' in message_lower:
            return 'pcm', 'sameness_to_trend', ""
        elif 'commonality_to_trend' in message_lower:
            return 'pcm', 'commonality_to_trend', ""
        elif 'to_trend' in message_lower:
            return 'pcm', 'to_trend', ""
        elif any(k in message_lower for k in ['trend', '트렌드', '차트', '그래프']):
            return 'pcm', 'trend', ""
        elif any(k in message_lower for k in ['commonality', '커먼', '공통']):
            return 'pcm', 'commonality', ""
        elif any(k in message_lower for k in ['sameness']):
            return 'pcm', 'sameness', ""
        elif any(k in message_lower for k in ['point', '포인트', 'site', '사이트']):
            return 'pcm', 'point', ""
        else:
            return 'pcm', 'trend', ""  # 기본값

    @classmethod
    def analyze_inline_query(cls, message_lower: str) -> tuple[str, str, str]:
        """INLINE choice에 대한 메시지 분석"""
        # 기준별 그룹화 요청 검사 (criteria-based analysis)
        criteria_keywords = ['별로', '기준으로', 'by', 'group by', 'main_eq', 'device', 'para', 'eq_cham', 'route', 'oper']
        if any(keyword in message_lower for keyword in criteria_keywords):
            # followup trend analysis로 라우팅 (criteria 기반 분석)
            return 'inline', 'trend_followup', ""
        
        # 초기 분석 키워드
        elif any(k in message_lower for k in ['initial', '초기', '처음']):
            return 'inline', 'trend_initial', ""
        
        # 성능 관련 키워드
        elif any(k in message_lower for k in ['performance', '성능', '모니터링']):
            return 'inline', 'performance', ""
        
        # 기본값을 trend_initial로 변경 (더 유용함)
        else:
            return 'inline', 'trend_initial', ""

    @classmethod
    def analyze_rag_query(cls, message_lower: str) -> tuple[str, str, str]:
        """RAG choice에 대한 메시지 분석"""
        rag_keywords = ['검색', 'search', '찾기', '조회', '문서', 'document', '파일', 'file']
        for keyword in rag_keywords:
            if keyword in message_lower:
                return 'rag', 'search', ""
        return 'rag', 'general', ""

    @classmethod
    def analyze_query(cls, message: str) -> tuple[str, str, str]:
        """
        메시지를 분석하여 어떤 타입의 처리가 필요한지 결정
        Returns: (data_type, command_type, error_message)
        """
        message_lower = message.lower().strip()
        
        # 빈 메시지 체크
        if not message_lower:
            return "", "", "메시지를 입력해주세요."
        
        # Two Tables 키워드는 choice='two'일 때만 처리하므로 여기서는 제거
        
        # RAG 관련 키워드 우선 검사
        rag_keywords = ['검색', 'search', '찾기', '조회', '문서', 'document', '파일', 'file', '설명', '요약', 'summary']
        for keyword in rag_keywords:
            if keyword in message_lower:
                return 'rag', 'search', ""
        
        # sameness_to_trend, commonality_to_trend 키워드 검사 (가장 구체적인 키워드부터 먼저 검사)
        if 'sameness_to_trend' in message_lower:
            return 'pcm', 'sameness_to_trend', ""
        elif 'commonality_to_trend' in message_lower:
            return 'pcm', 'commonality_to_trend', ""
        
        # PCM 관련 키워드 검사 (일반적인 키워드들은 나중에 검사)
        pcm_keywords = ['pcm', 'trend', '트렌드', '차트', '그래프', 'commonality', '커먼', '공통', 'sameness', 'point', '포인트', 'site', '사이트']
        for keyword in pcm_keywords:
            if keyword in message_lower:
                if any(k in message_lower for k in ['trend', '트렌드', '차트', '그래프']):
                    return 'pcm', 'trend', ""
                elif any(k in message_lower for k in ['commonality', '커먼', '공통']):
                    return 'pcm', 'commonality', ""
                elif any(k in message_lower for k in ['sameness']):
                    return 'pcm', 'sameness', ""
                elif any(k in message_lower for k in ['point', '포인트', 'site', '사이트']):
                    return 'pcm', 'point', ""
                else:
                    return 'pcm', 'trend', ""  # 기본값
        
        # INLINE 관련 키워드 검사
        inline_keywords = ['inline', 'trend', 'edit', 'cpk', 'achieve', '달성률']
        for keyword in inline_keywords:
            if keyword in message_lower:
                if any(k in message_lower for k in ['cpk', 'achieve', '달성률']):
                    return 'inline', 'cpk_achieve_rate_initial', ""
                elif any(k in message_lower for k in ['trend']):
                    return 'inline', 'trend', ""
                else:
                    return 'inline', 'edit', ""
        
        # 기본적으로 RAG로 처리 (질문이나 일반적인 요청)
        return 'rag', 'general', ""
