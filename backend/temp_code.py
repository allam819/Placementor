
@router.get("/recommend-dsa")
async def recommend_dsa_problem(user = Depends(verify_user)):
    from app.ai.dsa_selector import DSASelector
    supabase: Client = get_supabase_client()
    selector = DSASelector(supabase, user.user.id)
    recommendation = selector.recommend_problem()
    if not recommendation:
        raise HTTPException(status_code=404, detail="No suitable problems found in database")
    return recommendation
