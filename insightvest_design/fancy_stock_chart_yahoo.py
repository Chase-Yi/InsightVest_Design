from dotenv import load_dotenv

load_dotenv()

def render_fancy_stock_chart():
    # 确保所有必要的导入
    import streamlit as st
    import yfinance as yf
    from datetime import datetime, timedelta
    import pandas as pd
    import numpy as np
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    # 自定义CSS样式（黑金主题）
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            background: linear-gradient(to right, #BF953F, #FCF6BA, #D5AD36, #F3D261);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 1rem;
            text-shadow: 0 0 15px rgba(212, 175, 55, 0.4);
        }
        .sub-header {
            font-size: 1.5rem;
            background: linear-gradient(to right, #BF953F, #FCF6BA, #D5AD36, #F3D261);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            text-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
        }
        .info-box {
            background-color: rgba(28, 39, 60, 0.7);
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid rgba(212, 175, 55, 0.2);
        }
        .stat-container {
            display: flex;
            justify-content: space-between;
        }
        .stat-box {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            border: 1px solid rgba(255, 215, 0, 0.2);
            box-shadow: 0 0 12px rgba(255, 215, 0, 0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            width: 100%;
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        .stat-box:hover {
            transform: translateY(-3px);
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
        }
        .stat-box h4 {
            margin: 0;
            font-size: 1.2rem;
            color: #FFD700;
        }
        .stat-box p {
            font-size: 1.6rem;
            font-weight: bold;
            margin-top: 0.5rem;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='main-header'>🚀 高级股票可视化分析平台</h1>", unsafe_allow_html=True)

    # 创建边栏控制面板
    with st.sidebar:
        st.markdown("<h2 class='sub-header'>⚙️ 控制面板</h2>", unsafe_allow_html=True)
        ticker = st.text_input("输入股票代码", value="AAPL", key=f"stock_ticker_input_{st.session_state.get('section_selected', 'default')}")




        # 时间范围选择
        period_options = {
            "1个月": 30,
            "3个月": 90,
            "6个月": 180,
            "1年": 365,
            "2年": 730
        }
        selected_period = st.selectbox("选择时间范围", list(period_options.keys()))

        # 技术指标选择
        st.markdown("<h3 class='sub-header'>技术指标</h3>", unsafe_allow_html=True)
        show_ma = st.checkbox("移动平均线 (MA)", value=True)
        ma_periods = st.multiselect("MA周期", [5, 10, 20, 50, 100, 200], default=[20, 50, 200])

        show_volume = st.checkbox("成交量", value=True)
        show_rsi = st.checkbox("相对强弱指标 (RSI)", value=False)
        show_macd = st.checkbox("MACD指标", value=False)

        # 可视化样式
        st.markdown("<h3 class='sub-header'>可视化样式</h3>", unsafe_allow_html=True)
        chart_styles = ["传统", "现代科技", "专业交易", "暗黑模式", "清新绿色"]
        selected_style = st.selectbox("选择样式主题", chart_styles)

        analyze_button = st.button("🔍 开始分析", use_container_width=True)

    # 主界面
    if analyze_button or 'data' in st.session_state:
        try:
            # 获取数据
            end_date = datetime.today()
            start_date = end_date - timedelta(days=period_options[selected_period])

            # 显示加载中信息
            with st.spinner(f"正在加载 {ticker.upper()} 的历史数据..."):
                data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                # 修复 MultiIndex 列名问题
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)

                # 调试信息：打印数据
                st.write("调试信息：原始数据预览")
                st.write(data.head())
                st.write(f"数据行数: {len(data)}")

                # 将数据保存到会话状态中
                st.session_state.data = data
                st.session_state.ticker = ticker

            if data.empty:
                st.warning("⚠️ 没有找到该股票代码的数据，请检查后重试。")
                return

            # 检查 OHLC 列是否存在
            expected_columns = ['Open', 'High', 'Low', 'Close']
            available_columns = [col for col in data.columns if col in expected_columns]
            missing_columns = [col for col in expected_columns if col not in data.columns]

            if missing_columns:
                # 尝试小写列名
                column_mapping = {
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close'
                }
                for old_col, new_col in column_mapping.items():
                    if old_col in data.columns:
                        data[new_col] = data[old_col]
                        available_columns.append(new_col)

                # 重新检查缺失列
                missing_columns = [col for col in expected_columns if col not in data.columns]
                if missing_columns:
                    st.error(f"⚠️ 数据中缺少必要的 OHLC 列: {missing_columns}")
                    return

            # 数据清理：移除 NaN 值
            data = data.dropna(subset=['Open', 'High', 'Low', 'Close'])

            if data.empty:
                st.warning("⚠️ 数据清理后没有有效数据，请选择其他股票代码或时间范围。")
                return

            # 显示股票基本信息
            try:
                stock_info = yf.Ticker(ticker).info
                company_name = stock_info.get('longName', ticker.upper())
                current_price = stock_info.get('currentPrice', data['Close'].iloc[-1])
                previous_close = stock_info.get('previousClose', data['Close'].iloc[-2])
                price_change = current_price - previous_close
                price_change_percent = (price_change / previous_close) * 100

                # 价格信息显示
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"<h2>{company_name} ({ticker.upper()})</h2>", unsafe_allow_html=True)

                with col2:
                    price_color = "green" if price_change >= 0 else "red"
                    change_icon = "↑" if price_change >= 0 else "↓"
                    st.markdown(f"""
                    <div style='text-align: right'>
                        <h2 style='margin-bottom: 0px;'>${current_price:.2f}</h2>
                        <p style='color: {price_color}; font-size: 1.2rem; margin-top: 0px;'>
                            {change_icon} ${abs(price_change):.2f} ({price_change_percent:.2f}%)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                # 关键统计数据
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(f"""<div class='stat-box'>
                        <h4>52周最高</h4>
                        <p>{stock_info.get('fiftyTwoWeekHigh', 'N/A')}</p>
                    </div>""", unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""<div class='stat-box'>
                        <h4>52周最低</h4>
                        <p>{stock_info.get('fiftyTwoWeekLow', 'N/A')}</p>
                    </div>""", unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""<div class='stat-box'>
                        <h4>市值</h4>
                        <p>{stock_info.get('marketCap', 0) / 1e9:.2f}B</p>
                    </div>""", unsafe_allow_html=True)

                with col4:
                    st.markdown(f"""<div class='stat-box'>
                        <h4>成交量</h4>
                        <p>{stock_info.get('volume', 0) / 1e6:.1f}M</p>
                    </div>""", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"无法获取股票详细信息: {str(e)}")
                st.markdown(f"<h2>{ticker.upper()} - {selected_period}数据分析</h2>", unsafe_allow_html=True)

            # 计算技术指标
            # 计算移动平均线
            if show_ma:
                for period in ma_periods:
                    data[f'MA_{period}'] = data['Close'].rolling(window=period).mean()

            # 计算RSI
            if show_rsi:
                delta = data['Close'].diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                # 避免除零错误
                rs = avg_gain / avg_loss.replace(0, np.nan)
                data['RSI'] = 100 - (100 / (1 + rs.fillna(0)))

            # 计算MACD
            if show_macd:
                data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
                data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
                data['MACD'] = data['EMA12'] - data['EMA26']
                data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
                data['Histogram'] = data['MACD'] - data['Signal']

            # 确定需要创建的子图数量
            n_rows = 1
            if show_volume:
                n_rows += 1
            if show_rsi:
                n_rows += 1
            if show_macd:
                n_rows += 1

            # 设置子图的行高比例
            row_heights = [0.6]  # 主图（K线图）
            if show_volume:
                row_heights.append(0.1)
            if show_rsi:
                row_heights.append(0.15)
            if show_macd:
                row_heights.append(0.15)

            # 确保 row_heights 总和为 1
            total_height = sum(row_heights)
            row_heights = [h / total_height for h in row_heights]

            # 创建子图
            fig = make_subplots(
                rows=n_rows,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=row_heights
            )

            # 根据选择的样式设置图表颜色
            if selected_style == "传统":
                increasing_color = 'red'
                decreasing_color = 'green'
                bg_color = 'white'
                grid_color = 'lightgrey'
                text_color = 'black'
                ma_colors = ['blue', 'orange', 'purple', 'brown', 'pink', 'cyan']
            elif selected_style == "现代科技":
                increasing_color = '#00FFAA'
                decreasing_color = '#FF5733'
                bg_color = '#111111'
                grid_color = '#333333'
                text_color = 'white'
                ma_colors = ['#00BFFF', '#FFAA00', '#AA00FF', '#FF00AA', '#00FFFF', '#FFFF00']
            elif selected_style == "专业交易":
                increasing_color = '#53B987'
                decreasing_color = '#EB4D5C'
                bg_color = '#131722'
                grid_color = '#2A2E39'
                text_color = '#D6D6D6'
                ma_colors = ['#5D7CC9', '#FFBF00', '#FF6363', '#4CAF50', '#9C27B0', '#00E5FF']
            elif selected_style == "暗黑模式":
                increasing_color = '#0ECB81'
                decreasing_color = '#F6465D'
                bg_color = '#0B0E11'
                grid_color = '#1C2030'
                text_color = '#EEF0F3'
                ma_colors = ['#7B68EE', '#FFD700', '#87CEEB', '#FF69B4', '#20B2AA', '#FF8C00']
            elif selected_style == "清新绿色":
                increasing_color = '#3D9970'
                decreasing_color = '#FF4136'
                bg_color = '#F5F8F5'
                grid_color = '#E0E5E0'
                text_color = '#2C3E50'
                ma_colors = ['#0074D9', '#FF851B', '#F012BE', '#2ECC40', '#B10DC9', '#AAAAAA']

            # 绘制K线图
            fig.add_trace(
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    increasing_line_color=increasing_color,
                    decreasing_line_color=decreasing_color,
                    name='K线'
                ),
                row=1, col=1
            )

            # 添加移动平均线
            if show_ma:
                for i, period in enumerate(ma_periods):
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data[f'MA_{period}'],
                            line=dict(color=ma_colors[i % len(ma_colors)], width=1),
                            name=f'MA {period}'
                        ),
                        row=1, col=1
                    )

            # 添加成交量
            current_row = 2
            if show_volume:
                colors = [increasing_color if data['Close'].iloc[i] > data['Open'].iloc[i] else decreasing_color for i in range(len(data))]
                fig.add_trace(
                    go.Bar(
                        x=data.index,
                        y=data['Volume'],
                        marker_color=colors,
                        name='成交量'
                    ),
                    row=current_row, col=1
                )
                current_row += 1

            # 添加RSI
            if show_rsi:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['RSI'],
                        line=dict(color='#FF9900', width=1),
                        name='RSI'
                    ),
                    row=current_row, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=[70] * len(data.index),
                        line=dict(color='red', width=1, dash='dash'),
                        name='超买线'
                    ),
                    row=current_row, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=[30] * len(data.index),
                        line=dict(color='green', width=1, dash='dash'),
                        name='超卖线'
                    ),
                    row=current_row, col=1
                )
                current_row += 1

            # 添加MACD
            if show_macd:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['MACD'],
                        line=dict(color='#FF9900', width=1),
                        name='MACD'
                    ),
                    row=current_row, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['Signal'],
                        line=dict(color='#00BFFF', width=1),
                        name='信号线'
                    ),
                    row=current_row, col=1
                )
                colors = [increasing_color if val > 0 else decreasing_color for val in data['Histogram']]
                fig.add_trace(
                    go.Bar(
                        x=data.index,
                        y=data['Histogram'],
                        marker_color=colors,
                        name='MACD柱状图'
                    ),
                    row=current_row, col=1
                )

            # 更新布局
            fig.update_layout(
                title=f"{ticker.upper()} - {selected_period}历史走势",
                xaxis_title="日期",
                yaxis_title="价格",
                xaxis_rangeslider_visible=False,
                template="plotly_white" if bg_color == 'white' else "plotly_dark",
                height=800,
                margin=dict(t=50, l=20, r=20, b=30),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                ),
                paper_bgcolor=bg_color,
                plot_bgcolor=bg_color,
                font=dict(color=text_color)
            )

            # 更新x轴和y轴样式
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor=grid_color,
                zeroline=False
            )

            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor=grid_color,
                zeroline=False
            )

            # 显示图表
            st.plotly_chart(fig, use_container_width=True)

            # 使用 GPT 生成技术分析摘要
            def get_gpt_summary(prompt: str) -> str:
                from langchain.chat_models import ChatOpenAI
                try:
                    llm = ChatOpenAI(model="gpt-4", temperature=0.5)
                    result = llm.invoke(prompt)
                    return result.content if hasattr(result, "content") else str(result)
                except Exception as e:
                    return f"⚠️ GPT 分析生成失败：{e}"

            def generate_tech_summary_gpt(ticker, current_price, ma20, ma50, rsi, macd, signal):
                ma20_str = f"{ma20:.2f}" if pd.notna(ma20) else "N/A"
                ma50_str = f"{ma50:.2f}" if pd.notna(ma50) else "N/A"
                rsi_str = f"{rsi:.2f}" if pd.notna(rsi) else "N/A"
                macd_str = f"{macd:.2f}" if pd.notna(macd) else "N/A"
                signal_str = f"{signal:.2f}" if pd.notna(signal) else "N/A"
                prompt = f"""
                你是一名金融分析师，请根据以下指标用中文写一段简洁易懂的技术分析摘要：
                股票代码：{ticker}
                当前价格：{current_price:.2f}
                MA20：{ma20_str}
                MA50：{ma50_str}
                RSI：{rsi_str}
                MACD：{macd_str}
                Signal：{signal_str}

                写作要求：

                趋势判断：用"上涨/下跌/横盘"等明确词汇，配合生活化比喻（如：像爬坡/下楼梯/平路散步）
                
                指标解读：每个指标都要用新手能理解的比喻说明（例如：均线好比...）
                
                操作建议：给出"现在适合/不适合"的明确建议，用红绿灯比喻：
                
                绿灯：可以考虑买入/加仓
                
                黄灯：建议观望等待
                
                红灯：考虑卖出/谨慎
                
                风险提示：必须包含"投资有风险"的提醒
                
                语言风格：像朋友聊天一样自然，避免专业术语，多用问句引发思考
                
                字数：250-300字，分3-4个自然段
                
                示例结构：
                "XX股票现在处在...趋势（比喻说明）。就像...（生活化类比）...
                20日均线显示...（解释含义），这意味着...
                考虑到当前RSI指标...（解释超买/超卖），MACD显示...
                给您的建议是...（红绿灯建议），因为...
                记住：市场像天气会变化，建议..."
                
                请特别注意：所有专业概念必须转化为日常生活中的类比，让完全不懂股票的人也能立即明白。
                
                【优化说明】
                
                增加了明确的指标解释括号，帮助用户理解原始数据
                
                引入"红绿灯"系统，比专业术语更直观
                
                要求生活化比喻和问句互动，增强可读性
                
                强调风险提示的强制性
                
                提供示例结构规范输出格式
                
                特别禁止使用专业术语，确保小白友好
                
                增加了字数范围控制信息密度
                """
                return get_gpt_summary(prompt)

            # 显示 GPT 生成的技术分析摘要
            if len(data) > 50:
                st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                st.markdown("<h3>📊 技术分析摘要</h3>", unsafe_allow_html=True)

                # 提取指标值
                current_price = data['Close'].iloc[-1] if not data['Close'].empty else np.nan
                ma20 = data['MA_20'].iloc[-1] if show_ma and 'MA_20' in data else np.nan
                ma50 = data['MA_50'].iloc[-1] if show_ma and 'MA_50' in data else np.nan
                rsi = data['RSI'].iloc[-1] if show_rsi and 'RSI' in data else np.nan
                macd = data['MACD'].iloc[-1] if show_macd and 'MACD' in data else np.nan
                signal = data['Signal'].iloc[-1] if show_macd and 'Signal' in data else np.nan

                # 调用 GPT 生成分析摘要
                gpt_summary = generate_tech_summary_gpt(
                    ticker=ticker,
                    current_price=current_price,
                    ma20=ma20,
                    ma50=ma50,
                    rsi=rsi,
                    macd=macd,
                    signal=signal
                )
                st.markdown(gpt_summary)

                st.markdown("</div>", unsafe_allow_html=True)

                # 价格历史数据表格
                with st.expander("查看历史数据"):
                    st.dataframe(data.sort_index(ascending=False))

        except Exception as e:
            st.error(f"加载图表时出错: {str(e)}")
            st.write("💡 **提示**：请尝试以下操作：")
            st.write("- 检查股票代码是否正确（例如，'AAPL' 表示苹果公司）。")
            st.write("- 选择其他时间范围（如 '1个月' 或 '1年'）。")
            st.write("- 确保网络连接正常，或稍后重试。")
            st.write("调试信息（供高级用户参考）：")
            st.write(f"- 股票代码: {ticker}")
            st.write(f"- 时间范围: 从 {start_date} 到 {end_date}")
            st.write(f"- 数据是否为空: {'是' if data.empty else '否'}")
            if not data.empty:
                st.write(f"- 数据列名: {list(data.columns)}")
                st.write(f"- 数据行数: {len(data)}")
    else:
        # 首次加载界面的默认显示内容
        st.markdown("""
        <div class='info-box'>
            <h3>👋 欢迎使用高级股票可视化分析平台</h3>
            <p>使用左侧控制面板输入股票代码并选择您感兴趣的技术指标和时间范围，然后点击"开始分析"按钮查看详细图表。</p>
            <p>支持的功能:</p>
            <ul>
                <li>高级K线图和蜡烛图展示</li>
                <li>多种移动平均线(MA)指标</li>
                <li>成交量分析</li>
                <li>RSI超买超卖指标</li>
                <li>MACD趋势指标</li>
                <li>多种可视化主题风格</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # 添加一些常用股票代码示例
        st.markdown("<h3 class='sub-header'>热门股票代码示例</h3>", unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            **科技股**
            - AAPL (苹果)
            - MSFT (微软)
            - GOOGL (谷歌)
            - AMZN (亚马逊)
            """)

        with col2:
            st.markdown("""
            **金融股**
            - JPM (摩根大通)
            - BAC (美国银行)
            - V (Visa)
            - MA (万事达)
            """)

        with col3:
            st.markdown("""
            **消费股**
            - KO (可口可乐)
            - PG (宝洁)
            - MCD (麦当劳)
            - NKE (耐克)
            """)

        with col4:
            st.markdown("""
            **中国股票**
            - BABA (阿里巴巴)
            - PDD (拼多多)
            - NIO (蔚来)
            - BIDU (百度)
            """)