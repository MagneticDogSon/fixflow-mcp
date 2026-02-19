    parser.add_argument("--host", default="0.0.0.0", help="Host for SSE")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)), help="Port for SSE")
    
    args = parser.parse_args()

    if args.transport == "sse":
        sys.stderr.write(f"🚀 Starting FixFlow SSE server on {args.host}:{args.port}\n")
        mcp.run(transport='sse', host=args.host, port=args.port)
